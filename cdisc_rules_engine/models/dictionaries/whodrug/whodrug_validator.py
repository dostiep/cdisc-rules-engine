from cdisc_rules_engine.interfaces.cache_service_interface import CacheServiceInterface
from cdisc_rules_engine.interfaces.data_service_interface import DataServiceInterface
from cdisc_rules_engine.models.dictionaries.base_dictionary_validator import (
    BaseDictionaryValidator,
)
from cdisc_rules_engine.models.dictionaries.whodrug.whodrug_terms_factory import (
    WhoDrugTermsFactory,
)


class WhoDrugValidator(BaseDictionaryValidator):
    def __init__(
        self,
        data_service: DataServiceInterface = None,
        cache_service: CacheServiceInterface = None,
        **kwargs,
    ):
        self.cache_service = cache_service
        self.data_service = data_service
        self.path = kwargs.get("whodrug_path")
        self.term_dictionary = kwargs.get("terms")
        self.terms_factory = WhoDrugTermsFactory(self.data_service)

    def is_valid_term(
        self, term: str, term_type: str = "", variable: str = "", **kwargs
    ) -> bool:
        """
        Method to identify whether a term is valid based on its term type.

        Args:
            term: The dictionary term used
            term_type: The term type to validate against
            variable: The variable used to source the term data
            kwargs: Additional validator specific variables

        Returns:
            True: The term is valid
            False: The term is not valid
        """
        term_dictionary = self.get_term_dictionary()
        case_sensitive_check = kwargs.get("case_sensitive")
        if case_sensitive_check:
            return term in term_dictionary.get(term_type, {})
        else:
            for key in term_dictionary.get(term_type, {}):
                if key.lower() == term.lower():
                    return True
            return False