from modules.errors import ProgramError


class SkillBuilderError(ProgramError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
