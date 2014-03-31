import foxpath
from foxpath import test
#f="dfid-tz.xml"
f='sida-tz.xml'
#t='at least one (sector[@vocabulary="DAC"]/@code or sector[not(@vocabulary)]/@code) is on list Sector?'
t='at least one country-budget-items[@vocabulary="1"]/budget-item/@code is on list BudgetIdentifier (if activity-status/@code is at least 2 and (default-aid-type/@code or transaction/aid-type/@code is not A01 or A02))?'
#t='at least one country-budget-items[@vocabulary="1"]/budget-item/@code is on list BudgetIdentifier?'
#t="default-aid-type/@code or transaction/aid-type/@code is on list AidType (if activity-status/@code is at least 2)?"
lists={'Sector': ['13040'], 'BudgetIdentifier': ['5.1.1'], 'AidType': ['A01']}
test.test_doc_lists(f,t,lists)
