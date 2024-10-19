from enum import Enum


class CustomerIntent(str, Enum):
    GENERAL_QUESTION = "general/question"
    PRODUCT_QUESTION = "product/question"
    BILLING_INVOICE = "billing/invoice"
    REFUND_REQUEST = "refund/request"

    @property
    def escalate(self) -> bool:
        return self in {
            self.REFUND_REQUEST,
        }


class InternalIntent(str, Enum):
    IT_SUPPORT = "it/support"
    SOFTWARE_REQUEST = "software/request"
    POLICY_QUESTION = "policy/question"
    ACCESS_MANAGEMENT = "access/management"
    HARDWARE_ISSUE = "hardware/issue"

    @property
    def escalate(self) -> bool:
        return self in {
            self.ACCESS_MANAGEMENT,
        }
