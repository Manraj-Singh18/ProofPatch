"""Safe fixture used only to document the security-test boundary.

ProofPatch does not execute exploit payloads here. The regression verifies that
passing unit tests or unrelated Git evidence cannot establish a SQL-injection
absence claim.
"""


QUERY_WITH_BOUND_PARAMETERS = "SELECT * FROM users WHERE id = ?"
