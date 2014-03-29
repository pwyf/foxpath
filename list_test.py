import foxpath
from foxpath import test
#f="dfid-tz.xml"
f='sida-tz.xml'
#t='at least one (sector[@vocabulary="DAC"]/@code or sector[not(@vocabulary)]/@code) is on list Sector?'
t='at least one country-budget-items[@vocabulary="1"]/budget-item/@code is on list BudgetIdentifier?'
lists={'Sector': ['13040'], 'BudgetIdentifier': ['5.1.1']}
test.test_doc_lists(f,t,lists)
