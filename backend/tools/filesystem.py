from pathlib import Path


class FileSystemTool:

    @staticmethod
    def read(path: str):

        p = Path(path)

        if not p.exists():
            return ""

        return p.read_text(
            encoding="utf-8"
        )

    @staticmethod
    def write(
        path: str,
        content: str
    ):

        p = Path(path)

        p.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        p.write_text(
            content,
            encoding="utf-8"
        )

    @staticmethod
    def list_files(path: str):

        p = Path(path)

        files = []

        for file in p.rglob("*"):

            if file.is_file():

                files.append(
                    str(file)
                )

        return files
