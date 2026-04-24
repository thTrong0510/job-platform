import re


class CVFormBuilder:

    EXPERIENCE_FIELDS = [
        "company", "position", "start_date", "end_date", "description"
    ]

    EDUCATION_FIELDS = [
        "school", "degree", "start_date", "end_date"
    ]

    PROJECT_FIELDS = [
        "name", "description"
    ]

    @staticmethod
    def build_from_request(form_data):

        def get_value(field):
            value = form_data.get(field)

            if isinstance(value, list):
                return value[0].strip() if value and value[0] else ""

            if isinstance(value, str):
                return value.strip()

            return ""

        return {
            "full_name": get_value("full_name"),
            "email": get_value("email"),
            "phone": get_value("phone"),
            "location": get_value("location"),
            "summary": get_value("summary"),
            "experiences": CVFormBuilder._extract_section(
                form_data,
                "experiences",
                CVFormBuilder.EXPERIENCE_FIELDS
            ),
            "educations": CVFormBuilder._extract_section(
                form_data,
                "educations",
                CVFormBuilder.EDUCATION_FIELDS
            ),
            "projects": CVFormBuilder._extract_section(
                form_data,
                "projects",
                CVFormBuilder.PROJECT_FIELDS
            ),
        }

    @staticmethod
    def _extract_section(form_data, section_name, allowed_fields):
        pattern = re.compile(rf"{section_name}\[(\d+)\]\[(\w+)\]")
        data = {}

        for key, value in form_data.items():
            match = pattern.match(key)
            if not match:
                continue

            index = int(match.group(1))
            field = match.group(2)

            if field not in allowed_fields:
                continue

            if index not in data:
                data[index] = {f: "" for f in allowed_fields}

            # xử lý cả list và string
            if isinstance(value, list):
                clean_value = value[0].strip() if value and value[0] else ""
            elif isinstance(value, str):
                clean_value = value.strip()
            else:
                clean_value = ""

            data[index][field] = clean_value

        result = []

        for index in sorted(data.keys()):
            if any(data[index][f] for f in allowed_fields):
                result.append(data[index])

        return result

    @staticmethod
    def build_from_req(form_data):

        def get_value(field):
            return form_data.get(field, [""])[0]

        # =========================
        # BASIC INFO
        # =========================
        data = {
            "full_name": get_value("full_name"),
            "email": get_value("email"),
            "phone": get_value("phone"),
            "location": get_value("location"),
            "summary": get_value("summary"),
            "experiences": [],
            "educations": [],
            "projects": []
        }

        # =========================
        # GROUPED FIELDS PARSER
        # =========================

        pattern = re.compile(r"(\w+)\[(\d+)\]\[(\w+)\]")

        grouped = {}

        for key, value in form_data.items():
            match = pattern.match(key)
            if not match:
                continue

            section, index, field = match.groups()
            index = int(index)

            if section not in grouped:
                grouped[section] = {}

            if index not in grouped[section]:
                grouped[section][index] = {}

            grouped[section][index][field] = value[0]

        # =========================
        # BUILD EXPERIENCES
        # =========================
        if "experiences" in grouped:
            for index in sorted(grouped["experiences"].keys()):
                exp = grouped["experiences"][index]
                if exp.get("company", "").strip():
                    data["experiences"].append({
                        "company": exp.get("company", ""),
                        "position": exp.get("position", ""),
                        "start_date": exp.get("start_date", ""),
                        "end_date": exp.get("end_date", ""),
                        "description": exp.get("description", "")
                    })

        # =========================
        # BUILD EDUCATIONS
        # =========================
        if "educations" in grouped:
            for index in sorted(grouped["educations"].keys()):
                edu = grouped["educations"][index]
                if edu.get("school", "").strip():
                    data["educations"].append({
                        "school": edu.get("school", ""),
                        "degree": edu.get("degree", ""),
                        "start_date": edu.get("start_date", ""),
                        "end_date": edu.get("end_date", "")
                    })

        # =========================
        # BUILD PROJECTS
        # =========================
        if "projects" in grouped:
            for index in sorted(grouped["projects"].keys()):
                proj = grouped["projects"][index]
                if proj.get("name", "").strip():
                    data["projects"].append({
                        "name": proj.get("name", ""),
                        "description": proj.get("description", "")
                    })

        return data