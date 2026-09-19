"""Decision rules from binding addendum, called only after formal evaluation."""
from .core import Stop

def global_decision(states, d_revision_verified=False, pilot_verified=False,
                    legal_incompatibility=False, reproducible_access=True):
    if set(states)!=set('ABCDEF') or any(v not in ('PASS','REVISE','FAIL','INCONCLUSIVE') for v in states.values()):
        raise Stop('GATE_EVIDENCE_INCOMPLETE')
    if legal_incompatibility or not reproducible_access:
        return 'STOP'
    if any(states[k] in ('FAIL','INCONCLUSIVE') for k in 'ABC'):
        return 'STOP'
    if states['D'] in ('FAIL','INCONCLUSIVE') and not d_revision_verified:
        return 'STOP'
    if states['F'] in ('FAIL','INCONCLUSIVE') and not pilot_verified:
        return 'STOP'
    if all(v=='PASS' for v in states.values()):
        return 'GO'
    return 'GO_WITH_REVISION'
