"""
Tests for appform_sdk.xml2table — XML parsing and export.
"""

import os
import tempfile

from appform_sdk.xml2table import (
    _KNOWN_CLI_ARGS,
    _SIGN_TO_TYPE,
    _has_openpyxl,
    _has_pandas,
    _has_yaml,
    check_available_formats,
    collect_xml_data,
    create_markdown_table,
    create_sdk_yaml,
    find_xml_files,
    get_base_dir,
    parse_dynamic_scripts,
    parse_xml_to_table,
)

# ── Sample XML ───────────────────────────────────────────────────────────

SAMPLE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<appform>
  <i18ns>
    <i18n key="myapp.JH_CAS.label" zh="输入文件" />
    <i18n key="myapp.JH_NCPU.label" zh="CPU核数" />
  </i18ns>
  <jobSubmitConfigs>
    <jobSubmitConfig appId="myapp">
      <paramName>JH_CAS</paramName>
      <sign>upload</sign>
      <required>true</required>
      <validation></validation>
      <defaultValue>/home/user/default.cas</defaultValue>
    </jobSubmitConfig>
    <jobSubmitConfig appId="myapp">
      <paramName>JH_NCPU</paramName>
      <sign>text</sign>
      <required>true</required>
      <validation>^[0-9]+$</validation>
      <defaultValue>2</defaultValue>
    </jobSubmitConfig>
  </jobSubmitConfigs>
</appform>
"""


def _write_xml(content=SAMPLE_XML):
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False, encoding="utf-8"
    )
    f.write(content)
    f.close()
    return f.name


# ── _has_* dependency checks ─────────────────────────────────────────────


class TestHasDeps:
    def test_has_yaml(self):
        assert isinstance(_has_yaml(), bool)

    def test_has_pandas(self):
        assert isinstance(_has_pandas(), bool)

    def test_has_openpyxl(self):
        assert isinstance(_has_openpyxl(), bool)


# ── check_available_formats ──────────────────────────────────────────────


class TestCheckAvailableFormats:
    def test_returns_all_keys(self):
        fmts = check_available_formats()
        assert set(fmts.keys()) == {"yaml", "excel", "csv", "markdown"}

    def test_markdown_always_available(self):
        assert check_available_formats()["markdown"] is True


# ── parse_xml_to_table ───────────────────────────────────────────────────


class TestParseXmlToTable:
    def test_basic(self):
        xml_file = _write_xml()
        try:
            data, app_id = parse_xml_to_table(xml_file)
            assert len(data) == 2
            assert app_id == "myapp"
            assert data[0]["字段"] == "JH_CAS"
            assert data[0]["appid/应用 id"] == "myapp"
            assert data[0]["字段中文说明"] == "输入文件"
            assert data[0]["默认值"] == "/home/user/default.cas"
            assert data[0]["是否必填"] == "TRUE"
            assert data[0]["字段类型"] == "upload"
        finally:
            os.unlink(xml_file)

    def test_i18n_lookup(self):
        xml_file = _write_xml()
        try:
            data, _ = parse_xml_to_table(xml_file)
            cas_row = next(r for r in data if r["字段"] == "JH_CAS")
            ncpu_row = next(r for r in data if r["字段"] == "JH_NCPU")
            assert cas_row["字段中文说明"] == "输入文件"
            assert ncpu_row["字段中文说明"] == "CPU核数"
        finally:
            os.unlink(xml_file)

    def test_validation_and_required(self):
        xml_file = _write_xml()
        try:
            data, _ = parse_xml_to_table(xml_file)
            ncpu_row = next(r for r in data if r["字段"] == "JH_NCPU")
            assert ncpu_row["正则过滤字符"] == "^[0-9]+$"
            assert ncpu_row["是否必填"] == "TRUE"
        finally:
            os.unlink(xml_file)

    def test_empty_xml(self):
        xml_file = _write_xml("<appform></appform>")
        try:
            data, app_id = parse_xml_to_table(xml_file)
            assert data == []
            assert app_id == "unknown"
        finally:
            os.unlink(xml_file)

    def test_invalid_xml(self):
        xml_file = _write_xml("not xml at all")
        try:
            data, app_id = parse_xml_to_table(xml_file)
            assert data == []
            assert app_id == "error"
        finally:
            os.unlink(xml_file)

    def test_not_required(self):
        xml = """\
<?xml version="1.0"?>
<appform>
  <jobSubmitConfigs>
    <jobSubmitConfig appId="app1">
      <paramName>JH_OTHERS</paramName>
      <sign>text</sign>
      <required>false</required>
    </jobSubmitConfig>
  </jobSubmitConfigs>
</appform>
"""
        xml_file = _write_xml(xml)
        try:
            data, _ = parse_xml_to_table(xml_file)
            assert data[0]["是否必填"] == ""
        finally:
            os.unlink(xml_file)


# ── parse_dynamic_scripts ────────────────────────────────────────────────


class TestParseDynamicScripts:
    def test_no_script_dir(self, tmp_path):
        result = parse_dynamic_scripts(str(tmp_path), "myapp")
        assert result == {}

    def test_empty_script_dir(self, tmp_path):
        (tmp_path / "script").mkdir()
        result = parse_dynamic_scripts(str(tmp_path), "myapp")
        assert result == {}

    def test_parse_script(self, tmp_path):
        script_dir = tmp_path / "script"
        script_dir.mkdir()
        script = script_dir / "dynamic_JH_QUEUE.sh"
        script.write_text(
            'JH_QUEUE="normal|Normal Queue;gpu|GPU Queue"\n'
            'STAR_POST_SWITCH="on|Enable;off|Disable"\n'
            'OTHER_VAR="should_be_ignored"\n'
        )
        result = parse_dynamic_scripts(str(tmp_path), "myapp")
        assert "JH_QUEUE" in result
        assert result["JH_QUEUE"]["values"] == "normal;gpu"
        assert result["JH_QUEUE"]["labels"] == "Normal Queue;GPU Queue"
        assert "STAR_POST_SWITCH" in result
        assert "OTHER_VAR" not in result


# ── get_base_dir ─────────────────────────────────────────────────────────


class TestGetBaseDir:
    def test_script_dir_exists(self, tmp_path):
        app_dir = tmp_path / "app"
        (app_dir / "script").mkdir(parents=True)
        xml_file = app_dir / "config" / "view.xml"
        xml_file.parent.mkdir(parents=True)
        xml_file.write_text("<appform/>")
        result = get_base_dir(str(xml_file))
        assert result == str(app_dir)

    def test_no_script_dir(self, tmp_path):
        xml_file = tmp_path / "view.xml"
        xml_file.write_text("<appform/>")
        result = get_base_dir(str(xml_file))
        assert result == str(tmp_path)


# ── find_xml_files ───────────────────────────────────────────────────────


class TestFindXmlFiles:
    def test_recursive(self, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "view.xml").write_text("<appform/>")
        (tmp_path / "sub" / "view.xml").write_text("<appform/>")
        (tmp_path / "other.xml").write_text("<appform/>")
        (tmp_path / "package.xml").write_text("<appform/>")  # excluded
        result = find_xml_files(str(tmp_path), recursive=True)
        assert len(result) == 3  # view.xml, sub/view.xml, other.xml
        assert not any("package.xml" in f for f in result)

    def test_non_recursive(self, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "view.xml").write_text("<appform/>")
        (tmp_path / "sub" / "view.xml").write_text("<appform/>")
        result = find_xml_files(str(tmp_path), recursive=False)
        assert len(result) == 1

    def test_excludes_hidden_dirs(self, tmp_path):
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".hidden" / "view.xml").write_text("<appform/>")
        (tmp_path / "view.xml").write_text("<appform/>")
        result = find_xml_files(str(tmp_path), recursive=True)
        assert len(result) == 1

    def test_excludes_special_dirs(self, tmp_path):
        for d in ["node_modules", "__pycache__", "venv"]:
            (tmp_path / d).mkdir()
            (tmp_path / d / "view.xml").write_text("<appform/>")
        (tmp_path / "view.xml").write_text("<appform/>")
        result = find_xml_files(str(tmp_path), recursive=True)
        assert len(result) == 1


# ── collect_xml_data ─────────────────────────────────────────────────────


class TestCollectXmlData:
    def test_basic(self):
        xml_file = _write_xml()
        try:
            data, sources = collect_xml_data([xml_file])
            assert len(data) == 2
            assert sources == [xml_file]
        finally:
            os.unlink(xml_file)

    def test_empty_list(self):
        data, sources = collect_xml_data([])
        assert data == []
        assert sources == []

    def test_multiple_files(self):
        f1 = _write_xml()
        f2 = _write_xml()
        try:
            data, sources = collect_xml_data([f1, f2])
            assert len(data) == 4  # 2 params × 2 files
            assert len(sources) == 2
        finally:
            os.unlink(f1)
            os.unlink(f2)


# ── create_sdk_yaml ──────────────────────────────────────────────────────


class TestCreateSdkYaml:
    def test_basic(self, tmp_path):
        data, _ = parse_xml_to_table(_write_xml())
        out_file = str(tmp_path / "test.yaml")
        try:
            create_sdk_yaml(data, out_file)
        finally:
            for f in data:
                pass  # cleanup not needed for data
        assert os.path.exists(out_file)
        import yaml

        with open(out_file) as f:
            config = yaml.safe_load(f)
        assert "job_submit_config" in config
        apps = config["job_submit_config"]["applications"]
        assert "myapp" in apps
        params = apps["myapp"]["parameters"]
        assert len(params) == 2

    def test_cli_args_mapped(self, tmp_path):
        data, _ = parse_xml_to_table(_write_xml())
        out_file = str(tmp_path / "test.yaml")
        create_sdk_yaml(data, out_file)
        import yaml

        with open(out_file) as f:
            config = yaml.safe_load(f)
        params = config["job_submit_config"]["applications"]["myapp"]["parameters"]
        cas_param = next(p for p in params if p["name"] == "JH_CAS")
        assert cas_param.get("cli_arg") == "input"
        assert cas_param.get("short_arg") == "i"

    def test_empty_data(self, tmp_path, capsys):
        out_file = str(tmp_path / "empty.yaml")
        create_sdk_yaml([], out_file)
        assert not os.path.exists(out_file)
        assert "Warning" in capsys.readouterr().out


# ── create_markdown_table ────────────────────────────────────────────────


class TestCreateMarkdownTable:
    def test_basic(self, tmp_path):
        data = [
            {
                "appid/应用 id": "app1",
                "字段": "JH_CAS",
                "字段中文说明": "输入",
                "默认值": "",
                "字段类型": "upload",
                "是否必填": "TRUE",
                "正则过滤字符": "",
                "选项值": "",
                "选项显示": "",
                "源文件": "a.xml",
            },
        ]
        out_file = str(tmp_path / "test.md")
        create_markdown_table(data, out_file, ["a.xml"])
        assert os.path.exists(out_file)
        content = open(out_file).read()
        assert "表单配置汇总" in content
        assert "JH_CAS" in content
        assert "app1" in content
        assert "a.xml" in content

    def test_empty_data(self, tmp_path, capsys):
        out_file = str(tmp_path / "empty.md")
        create_markdown_table([], out_file)
        assert not os.path.exists(out_file)
        assert "Warning" in capsys.readouterr().out

    def test_pipe_escaping(self, tmp_path):
        data = [
            {
                "appid/应用 id": "app",
                "字段": "X|Y",
                "字段中文说明": "",
                "默认值": "",
                "字段类型": "",
                "是否必填": "",
                "正则过滤字符": "",
                "选项值": "",
                "选项显示": "",
                "源文件": "",
            },
        ]
        out_file = str(tmp_path / "esc.md")
        create_markdown_table(data, out_file)
        content = open(out_file).read()
        assert "X\\|Y" in content


# ── _SIGN_TO_TYPE / _KNOWN_CLI_ARGS mappings ────────────────────────────


class TestMappings:
    def test_sign_to_type_coverage(self):
        assert _SIGN_TO_TYPE["text"] == "text"
        assert _SIGN_TO_TYPE["upload"] == "upload"
        assert _SIGN_TO_TYPE["select"] == "select"
        assert _SIGN_TO_TYPE["switch"] == "switch"
        assert _SIGN_TO_TYPE["file"] == "upload"
        assert _SIGN_TO_TYPE["password"] == "text"

    def test_known_cli_args(self):
        assert _KNOWN_CLI_ARGS["JH_CAS"]["cli_arg"] == "input"
        assert _KNOWN_CLI_ARGS["JH_NCPU"]["cli_arg"] == "ncpu"
        assert _KNOWN_CLI_ARGS["JH_QUEUE"]["short_arg"] == "q"
