from pathlib import Path
from typing import Optional

from api_contract_validator.input.factory import register_parser, BaseInputParser
from api_contract_validator.input.normalizer.models import SourceType

from .parser import PRDParser
from api_contract_validator.config.exceptions import PRDParsingError


class PRDInputParser(BaseInputParser):
	"""
	Adapter that exposes the PRDParser through the BaseInputParser interface
	so it can be registered with the ParserRegistry. It defers actual NLP
	initialization errors and reports inability to parse gracefully.
	"""

	def __init__(self):
		self._inner: Optional[PRDParser] = None
		self._available = False
		try:
			self._inner = PRDParser()
			self._available = True
		except Exception as e:
			# Do not raise here — the registry should still return a parser
			# instance but it will report it cannot parse files.
			self._available = False

	def parse_file(self, file_path: Path):
		if not self._available or not self._inner:
			raise PRDParsingError("PRD parser not available (spaCy model missing?)")
		return self._inner.parse_file(Path(file_path))

	def get_source_type(self):
		return SourceType.PRD

	def can_parse(self, file_path: Path) -> bool:
		# Only claim to be able to parse common PRD formats when available
		if not self._available:
			return False
		return file_path.suffix.lower() in [".md", ".markdown", ".txt", ".docx"]


# Register this adapter with the global parser registry so parse_with_type_hint
# can auto-detect and use PRD files when present.
try:
	register_parser(SourceType.PRD, PRDInputParser)
except Exception:
	# Best-effort registration — avoid import-time failures
	pass
