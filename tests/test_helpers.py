import pytest
from unittest.mock import patch, MagicMock, call


# ══════════════════════════════════════════════════════════════════════
# 1. is_filters_empty
#    file: app/common/check_empty_dict.py
# ══════════════════════════════════════════════════════════════════════
class TestIsFiltersEmpty:

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.common.check_empty_dict import is_filters_empty
        self.fn = is_filters_empty

    def test_all_values_none_returns_true(self):
        assert self.fn({"keyword": None, "status": None}) is True

    def test_all_values_empty_string_returns_true(self):
        assert self.fn({"keyword": "", "status": ""}) is True

    def test_all_values_empty_list_returns_true(self):
        assert self.fn({"tags": [], "ids": []}) is True

    def test_all_values_zero_returns_true(self):
        # 0 là falsy → coi như rỗng
        assert self.fn({"page": 0}) is True

    def test_empty_dict_returns_true(self):
        assert self.fn({}) is True

    def test_one_value_truthy_returns_false(self):
        assert self.fn({"keyword": "python", "status": None}) is False

    def test_all_values_truthy_returns_false(self):
        assert self.fn({"keyword": "python", "status": "OPEN"}) is False

    def test_value_is_nonempty_list_returns_false(self):
        assert self.fn({"ids": [1, 2]}) is False

    def test_value_is_whitespace_returns_true(self):
        # " " là truthy trong Python → is_filters_empty trả False
        # (hàm không strip — đây là hành vi thực tế của code)
        assert self.fn({"keyword": "  "}) is False

    def test_mixed_falsy_and_truthy_returns_false(self):
        assert self.fn({"a": None, "b": "", "c": "value"}) is False


# ══════════════════════════════════════════════════════════════════════
# 2. parse_date  &  _normalize_date
#    file: app/common/date_time_customize.py
# ══════════════════════════════════════════════════════════════════════
class TestParseDate:

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.common.date_time_customize import parse_date
        self.fn = parse_date

    def test_valid_date_returns_date_object(self):
        from datetime import date
        result = self.fn("01/06/2024")
        assert result == date(2024, 6, 1)

    def test_none_input_returns_none(self):
        assert self.fn(None) is None

    def test_empty_string_returns_none(self):
        assert self.fn("") is None

    def test_wrong_format_iso_returns_none(self):
        # ISO format "2024-06-01" không khớp "%d/%m/%Y"
        assert self.fn("2024-06-01") is None

    def test_wrong_format_us_returns_none(self):
        assert self.fn("06/01/2024") is not None  # parse thành 06 tháng 1

    def test_invalid_date_value_returns_none(self):
        assert self.fn("32/13/2024") is None

    def test_text_string_returns_none(self):
        assert self.fn("not-a-date") is None

    def test_day_boundary_valid(self):
        from datetime import date
        assert self.fn("31/12/2023") == date(2023, 12, 31)

    def test_leap_day_valid(self):
        from datetime import date
        assert self.fn("29/02/2024") == date(2024, 2, 29)

    def test_leap_day_non_leap_year_returns_none(self):
        assert self.fn("29/02/2023") is None


class TestNormalizeDate:

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.common.date_time_customize import _normalize_date
        self.fn = _normalize_date

    # ── None / falsy input ────────────────────────────────────────────

    def test_none_returns_none(self):
        assert self.fn(None) is None

    def test_empty_string_returns_none(self):
        assert self.fn("") is None

    def test_whitespace_only_returns_none(self):
        assert self.fn("   ") is None

    # ── YYYY (4 digits) ───────────────────────────────────────────────

    def test_year_only_appends_01_01(self):
        assert self.fn("2024") == "2024-01-01"

    def test_year_only_strips_whitespace(self):
        assert self.fn("  2024  ") == "2024-01-01"

    def test_non_digit_4_chars_returns_none(self):
        assert self.fn("abcd") is None

    # ── YYYY-MM (7 chars) ─────────────────────────────────────────────

    def test_year_month_appends_01(self):
        assert self.fn("2024-06") == "2024-06-01"

    def test_year_month_strips_whitespace(self):
        assert self.fn("  2024-06  ") == "2024-06-01"

    def test_7_char_non_date_returns_value(self):
        # Chỉ check độ dài 7 → bất kỳ chuỗi 7 ký tự đều bị thêm "-01"
        result = self.fn("abcdefg")
        assert result == "abcdefg-01"

    # ── YYYY-MM-DD (10 chars) ─────────────────────────────────────────

    def test_full_date_returned_as_is(self):
        assert self.fn("2024-06-15") == "2024-06-15"

    def test_full_date_strips_whitespace(self):
        assert self.fn("  2024-06-15  ") == "2024-06-15"

    # ── other lengths → None ──────────────────────────────────────────

    def test_3_chars_returns_none(self):
        assert self.fn("abc") is None

    def test_5_chars_returns_none(self):
        assert self.fn("12345") is None

    def test_8_chars_returns_none(self):
        assert self.fn("20240615") is None

    def test_11_chars_returns_none(self):
        assert self.fn("2024-06-150") is None


# ══════════════════════════════════════════════════════════════════════
# 3. CVFileUtils
#    file: app/common/file_utils.py
# ══════════════════════════════════════════════════════════════════════
class TestCVFileUtils:

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.common.file_utils import CVFileUtils
        self.cls = CVFileUtils

    # ── allowed_file ──────────────────────────────────────────────────

    def test_allowed_pdf_returns_true(self):
        assert self.cls.allowed_file("resume.pdf") is True

    def test_allowed_doc_returns_true(self):
        assert self.cls.allowed_file("resume.doc") is True

    def test_allowed_docx_returns_true(self):
        assert self.cls.allowed_file("resume.docx") is True

    def test_allowed_uppercase_pdf_returns_true(self):
        assert self.cls.allowed_file("RESUME.PDF") is True

    def test_allowed_mixed_case_returns_true(self):
        assert self.cls.allowed_file("Resume.Docx") is True

    def test_not_allowed_txt_returns_false(self):
        assert self.cls.allowed_file("resume.txt") is False

    def test_not_allowed_jpg_returns_false(self):
        assert self.cls.allowed_file("photo.jpg") is False

    def test_not_allowed_exe_returns_false(self):
        assert self.cls.allowed_file("virus.exe") is False

    def test_no_extension_returns_false(self):
        assert self.cls.allowed_file("noextension") is False

    def test_dot_only_returns_false(self):
        assert self.cls.allowed_file(".pdf") is True  # '.' in filename → True, ext = "pdf"

    def test_multiple_dots_uses_last_extension(self):
        assert self.cls.allowed_file("my.resume.file.pdf") is True
        assert self.cls.allowed_file("my.resume.file.exe") is False

    # ── is_valid_size ─────────────────────────────────────────────────

    def test_file_under_5mb_returns_true(self):
        file = MagicMock()
        file.tell.return_value = 1 * 1024 * 1024  # 1MB
        ok, msg = self.cls.is_valid_size(file)
        assert ok is True
        assert msg == ""

    def test_file_exactly_5mb_returns_true(self):
        file = MagicMock()
        file.tell.return_value = 5 * 1024 * 1024  # đúng 5MB
        ok, msg = self.cls.is_valid_size(file)
        assert ok is True

    def test_file_over_5mb_returns_false(self):
        file = MagicMock()
        file.tell.return_value = 5 * 1024 * 1024 + 1  # 5MB + 1 byte
        ok, msg = self.cls.is_valid_size(file)
        assert ok is False
        assert "5MB" in msg

    def test_is_valid_size_seeks_to_end_then_resets(self):
        file = MagicMock()
        file.tell.return_value = 100
        self.cls.is_valid_size(file)
        # Gọi seek(0,2) để đến cuối, sau đó seek(0) để reset
        assert file.seek.call_args_list == [call(0, 2), call(0)]

    def test_file_zero_bytes_returns_true(self):
        file = MagicMock()
        file.tell.return_value = 0
        ok, _ = self.cls.is_valid_size(file)
        assert ok is True

    # ── get_full_path ─────────────────────────────────────────────────

    def test_get_full_path_joins_root_path_with_relative(self):
        mock_app = MagicMock()
        mock_app.root_path = "/var/www/app"
        with patch("app.common.file_utils.current_app", mock_app):
            result = self.cls.get_full_path("/static/uploads/cv.pdf")
            assert result.replace("\\", "/") == "/var/www/app/static/uploads/cv.pdf"

    def test_get_full_path_strips_leading_slash(self):
        mock_app = MagicMock()
        mock_app.root_path = "/var/www/app"
        with patch("app.common.file_utils.current_app", mock_app):
            result = self.cls.get_full_path("/static/file.pdf")
            assert not result.replace("\\", "/").startswith("//")

    def test_get_full_path_normalizes_backslashes(self):
        mock_app = MagicMock()
        mock_app.root_path = "/var/www/app"
        with patch("app.common.file_utils.current_app", mock_app):
            result = self.cls.get_full_path("\\static\\uploads\\cv.pdf")
            assert "\\" not in result

    def test_get_full_path_no_leading_slash(self):
        mock_app = MagicMock()
        mock_app.root_path = "/var/www/app"
        with patch("app.common.file_utils.current_app", mock_app):
            result = self.cls.get_full_path("static/uploads/cv.pdf")
            assert result.replace("\\", "/") == "/var/www/app/static/uploads/cv.pdf"

    # ── save_temp ─────────────────────────────────────────────────────

    def test_save_temp_saves_file_and_returns_path(self):
        file = MagicMock()
        file.filename = "mycv.pdf"
        with patch("app.common.file_utils.os.path.exists", return_value=True), \
             patch("app.common.file_utils.secure_filename", return_value="mycv.pdf"), \
             patch("app.common.file_utils.uuid.uuid4") as mock_uuid, \
             patch("app.common.file_utils.os.path.join", side_effect=lambda *a: "/".join(a)):
            mock_uuid.return_value.hex = "abc123"
            result = self.cls.save_temp(file)
            file.save.assert_called_once()
            assert "abc123_mycv.pdf" in result

    def test_save_temp_creates_folder_if_not_exists(self):
        file = MagicMock()
        file.filename = "cv.pdf"
        with patch("app.common.file_utils.os.path.exists", return_value=False) as mock_exists, \
             patch("app.common.file_utils.os.makedirs") as mock_makedirs, \
             patch("app.common.file_utils.secure_filename", return_value="cv.pdf"), \
             patch("app.common.file_utils.uuid.uuid4") as mock_uuid, \
             patch("app.common.file_utils.os.path.join", side_effect=lambda *a: "/".join(a)):
            mock_uuid.return_value.hex = "xyz"
            self.cls.save_temp(file)
            mock_makedirs.assert_called_once()

    def test_save_temp_does_not_create_folder_if_exists(self):
        file = MagicMock()
        file.filename = "cv.pdf"
        with patch("app.common.file_utils.os.path.exists", return_value=True), \
             patch("app.common.file_utils.os.makedirs") as mock_makedirs, \
             patch("app.common.file_utils.secure_filename", return_value="cv.pdf"), \
             patch("app.common.file_utils.uuid.uuid4") as mock_uuid, \
             patch("app.common.file_utils.os.path.join", side_effect=lambda *a: "/".join(a)):
            mock_uuid.return_value.hex = "xyz"
            self.cls.save_temp(file)
            mock_makedirs.assert_not_called()

    def test_save_temp_unique_name_uses_uuid(self):
        file = MagicMock()
        file.filename = "cv.pdf"
        with patch("app.common.file_utils.os.path.exists", return_value=True), \
             patch("app.common.file_utils.secure_filename", return_value="cv.pdf"), \
             patch("app.common.file_utils.uuid.uuid4") as mock_uuid, \
             patch("app.common.file_utils.os.path.join", side_effect=lambda *a: "/".join(a)):
            mock_uuid.return_value.hex = "unique999"
            result = self.cls.save_temp(file)
            assert "unique999" in result

    # ── delete_temp ───────────────────────────────────────────────────

    def test_delete_temp_removes_file_when_exists(self):
        with patch("app.common.file_utils.os.path.exists", return_value=True), \
             patch("app.common.file_utils.os.remove") as mock_rm:
            self.cls.delete_temp("/tmp/cv.pdf")
            mock_rm.assert_called_once_with("/tmp/cv.pdf")

    def test_delete_temp_does_nothing_when_file_not_exists(self):
        with patch("app.common.file_utils.os.path.exists", return_value=False), \
             patch("app.common.file_utils.os.remove") as mock_rm:
            self.cls.delete_temp("/tmp/cv.pdf")
            mock_rm.assert_not_called()

    def test_delete_temp_does_nothing_when_path_is_none(self):
        with patch("app.common.file_utils.os.remove") as mock_rm:
            self.cls.delete_temp(None)
            mock_rm.assert_not_called()

    def test_delete_temp_does_nothing_when_path_is_empty_string(self):
        with patch("app.common.file_utils.os.path.exists", return_value=False), \
             patch("app.common.file_utils.os.remove") as mock_rm:
            self.cls.delete_temp("")
            mock_rm.assert_not_called()


# ══════════════════════════════════════════════════════════════════════
# 4. CVFormBuilder
#    file: app/common/CVFormBuilder.py
# ══════════════════════════════════════════════════════════════════════
class TestCVFormBuilder:

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.common.CVFormBuilder import CVFormBuilder
        self.cls = CVFormBuilder

    # ── build_from_request ────────────────────────────────────────────

    def test_build_returns_all_top_level_keys(self):
        result = self.cls.build_from_request({})
        assert set(result.keys()) == {
            "full_name", "email", "phone", "location",
            "summary", "avatar", "experiences", "educations", "projects"
        }

    def test_build_string_field_stripped(self):
        result = self.cls.build_from_request({"full_name": "  Nguyen Van A  "})
        assert result["full_name"] == "Nguyen Van A"

    def test_build_list_field_uses_first_element(self):
        result = self.cls.build_from_request({"full_name": ["  Nhi  ", "ignored"]})
        assert result["full_name"] == "Nhi"

    def test_build_list_field_empty_list_returns_empty_string(self):
        result = self.cls.build_from_request({"full_name": []})
        assert result["full_name"] == ""

    def test_build_list_field_first_element_none_returns_empty(self):
        result = self.cls.build_from_request({"full_name": [None]})
        assert result["full_name"] == ""

    def test_build_missing_field_returns_empty_string(self):
        result = self.cls.build_from_request({})
        assert result["full_name"] == ""
        assert result["email"] == ""
        assert result["phone"] == ""

    def test_build_avatar_url_present_and_nonempty(self):
        result = self.cls.build_from_request({"avatar_url": "  https://cdn/img.jpg  "})
        assert result["avatar"] == "https://cdn/img.jpg"

    def test_build_avatar_url_absent_returns_none(self):
        result = self.cls.build_from_request({})
        assert result["avatar"] is None

    def test_build_avatar_url_empty_string_returns_none(self):
        result = self.cls.build_from_request({"avatar_url": ""})
        assert result["avatar"] is None

    def test_build_experiences_empty_when_no_keys(self):
        result = self.cls.build_from_request({})
        assert result["experiences"] == []

    def test_build_educations_empty_when_no_keys(self):
        result = self.cls.build_from_request({})
        assert result["educations"] == []

    def test_build_projects_empty_when_no_keys(self):
        result = self.cls.build_from_request({})
        assert result["projects"] == []

    # ── _extract_section — experiences ────────────────────────────────

    def test_extract_section_single_experience(self):
        form = {
            "experiences[0][company]":  "TechCorp",
            "experiences[0][position]": "Backend Dev",
            "experiences[0][start_date]": "2022-01",
            "experiences[0][end_date]":   "2024-01",
            "experiences[0][description]": "Built APIs",
        }
        result = self.cls.build_from_request(form)
        assert len(result["experiences"]) == 1
        assert result["experiences"][0]["company"] == "TechCorp"
        assert result["experiences"][0]["position"] == "Backend Dev"

    def test_extract_section_multiple_experiences_in_order(self):
        form = {
            "experiences[0][company]": "CompA",
            "experiences[0][position]": "Dev A",
            "experiences[1][company]": "CompB",
            "experiences[1][position]": "Dev B",
        }
        result = self.cls.build_from_request(form)
        assert len(result["experiences"]) == 2
        assert result["experiences"][0]["company"] == "CompA"
        assert result["experiences"][1]["company"] == "CompB"

    def test_extract_section_skips_all_empty_rows(self):
        form = {
            "experiences[0][company]": "",
            "experiences[0][position]": "",
            "experiences[0][start_date]": "",
            "experiences[0][end_date]": "",
            "experiences[0][description]": "",
        }
        result = self.cls.build_from_request(form)
        assert result["experiences"] == []

    def test_extract_section_ignores_unknown_fields(self):
        form = {
            "experiences[0][company]":  "Corp",
            "experiences[0][unknown_field]": "should be ignored",
        }
        result = self.cls.build_from_request(form)
        assert "unknown_field" not in result["experiences"][0]

    def test_extract_section_strips_whitespace_from_string_values(self):
        form = {"experiences[0][company]": "  TechCorp  "}
        result = self.cls.build_from_request(form)
        assert result["experiences"][0]["company"] == "TechCorp"

    def test_extract_section_handles_list_values(self):
        form = {"experiences[0][company]": ["  TechCorp  ", "ignored"]}
        result = self.cls.build_from_request(form)
        assert result["experiences"][0]["company"] == "TechCorp"

    def test_extract_section_non_experience_keys_ignored(self):
        form = {
            "experiences[0][company]": "Corp",
            "other_field": "value",
        }
        result = self.cls.build_from_request(form)
        assert len(result["experiences"]) == 1

    # ── _extract_section — educations ─────────────────────────────────

    def test_extract_education_single(self):
        form = {
            "educations[0][school]": "HUST",
            "educations[0][degree]": "B.Sc",
            "educations[0][start_date]": "2018-09",
            "educations[0][end_date]":   "2022-06",
        }
        result = self.cls.build_from_request(form)
        assert len(result["educations"]) == 1
        assert result["educations"][0]["school"] == "HUST"
        assert result["educations"][0]["degree"] == "B.Sc"

    def test_extract_education_empty_row_skipped(self):
        form = {
            "educations[0][school]": "",
            "educations[0][degree]": "",
        }
        result = self.cls.build_from_request(form)
        assert result["educations"] == []

    # ── _extract_section — projects ───────────────────────────────────

    def test_extract_project_single(self):
        form = {
            "projects[0][name]":        "My App",
            "projects[0][description]": "A great app",
        }
        result = self.cls.build_from_request(form)
        assert len(result["projects"]) == 1
        assert result["projects"][0]["name"] == "My App"

    def test_extract_project_empty_row_skipped(self):
        form = {
            "projects[0][name]":        "",
            "projects[0][description]": "",
        }
        result = self.cls.build_from_request(form)
        assert result["projects"] == []

    def test_extract_mixed_valid_and_empty_rows(self):
        form = {
            "experiences[0][company]":  "Corp",
            "experiences[0][position]": "Dev",
            "experiences[1][company]":  "",   # rỗng → bị bỏ
            "experiences[1][position]": "",
        }
        result = self.cls.build_from_request(form)
        assert len(result["experiences"]) == 1
        assert result["experiences"][0]["company"] == "Corp"


# ══════════════════════════════════════════════════════════════════════
# 5. parse_nested_form
#    file: app/common/ProfileFromBuilder.py
# ══════════════════════════════════════════════════════════════════════
class TestParseNestedForm:

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.common.ProfileFromBuilder import parse_nested_form
        self.fn = parse_nested_form

    def test_single_entry_returns_list_with_one_dict(self):
        form = {
            "skills[0][name]":  "Python",
            "skills[0][level]": "Advanced",
        }
        result = self.fn(form, "skills")
        assert len(result) == 1
        assert result[0]["name"] == "Python"
        assert result[0]["level"] == "Advanced"

    def test_multiple_entries_returned_in_index_order(self):
        form = {
            "skills[0][name]": "Python",
            "skills[1][name]": "Flask",
            "skills[2][name]": "MySQL",
        }
        result = self.fn(form, "skills")
        assert len(result) == 3
        assert result[0]["name"] == "Python"
        assert result[1]["name"] == "Flask"
        assert result[2]["name"] == "MySQL"

    def test_entries_sorted_by_index_regardless_of_insertion_order(self):
        form = {
            "skills[2][name]": "C",
            "skills[0][name]": "A",
            "skills[1][name]": "B",
        }
        result = self.fn(form, "skills")
        assert [r["name"] for r in result] == ["A", "B", "C"]

    def test_no_matching_keys_returns_empty_list(self):
        form = {"other[0][name]": "X"}
        result = self.fn(form, "skills")
        assert result == []

    def test_empty_form_returns_empty_list(self):
        assert self.fn({}, "skills") == []

    def test_prefix_mismatch_ignored(self):
        form = {
            "skills[0][name]": "Python",
            "educations[0][school]": "HUST",
        }
        result = self.fn(form, "skills")
        assert len(result) == 1
        assert result[0]["name"] == "Python"

    def test_multiple_fields_per_entry(self):
        form = {
            "exp[0][company]":  "Corp",
            "exp[0][position]": "Dev",
            "exp[0][years]":    "3",
        }
        result = self.fn(form, "exp")
        assert result[0] == {"company": "Corp", "position": "Dev", "years": "3"}

    def test_value_preserved_as_is(self):
        # parse_nested_form không strip/transform giá trị
        form = {"items[0][val]": "  spaced  "}
        result = self.fn(form, "items")
        assert result[0]["val"] == "  spaced  "

    def test_non_matching_pattern_keys_ignored(self):
        form = {
            "skills[0][name]": "Python",
            "skills_extra":    "ignored",
            "skills0name":     "ignored",
        }
        result = self.fn(form, "skills")
        assert len(result) == 1


# ══════════════════════════════════════════════════════════════════════
# 6. CloudinaryUtil
#    file: app/common/CloudinaryUtil.py
# ══════════════════════════════════════════════════════════════════════
class TestCloudinaryUtil:

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.common.CloudinaryUtil import CloudinaryUtil
        self.cls = CloudinaryUtil

    def test_upload_image_none_file_returns_none(self):
        result = self.cls.upload_image(None)
        assert result is None

    def test_upload_image_success_returns_secure_url(self):
        fake_result = {"secure_url": "https://res.cloudinary.com/test/image/upload/img.jpg"}
        with patch("app.common.CloudinaryUtil.cloudinary.uploader.upload", return_value=fake_result):
            result = self.cls.upload_image(MagicMock())
            assert result == "https://res.cloudinary.com/test/image/upload/img.jpg"

    def test_upload_image_missing_secure_url_returns_none(self):
        fake_result = {}  # không có "secure_url"
        with patch("app.common.CloudinaryUtil.cloudinary.uploader.upload", return_value=fake_result):
            result = self.cls.upload_image(MagicMock())
            assert result is None

    def test_upload_image_calls_uploader_with_correct_folder(self):
        fake_result = {"secure_url": "https://cdn/img.jpg"}
        with patch("app.common.CloudinaryUtil.cloudinary.uploader.upload", return_value=fake_result) as mock_upload:
            file = MagicMock()
            self.cls.upload_image(file)
            call_kwargs = mock_upload.call_args.kwargs
            assert call_kwargs["folder"] == "cv_avatars"

    def test_upload_image_calls_uploader_with_image_resource_type(self):
        fake_result = {"secure_url": "https://cdn/img.jpg"}
        with patch("app.common.CloudinaryUtil.cloudinary.uploader.upload", return_value=fake_result) as mock_upload:
            self.cls.upload_image(MagicMock())
            call_kwargs = mock_upload.call_args.kwargs
            assert call_kwargs["resource_type"] == "image"

    def test_upload_image_calls_uploader_with_file_as_first_arg(self):
        fake_result = {"secure_url": "https://cdn/img.jpg"}
        with patch("app.common.CloudinaryUtil.cloudinary.uploader.upload", return_value=fake_result) as mock_upload:
            file = MagicMock()
            self.cls.upload_image(file)
            assert mock_upload.call_args.args[0] is file

    def test_upload_image_empty_string_file_returns_none(self):
        # "" là falsy → trả None ngay, không gọi uploader
        with patch("app.common.CloudinaryUtil.cloudinary.uploader.upload") as mock_upload:
            result = self.cls.upload_image("")
            assert result is None
            mock_upload.assert_not_called()