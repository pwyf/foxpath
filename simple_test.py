import foxpath
from foxpath import test
f="dfid-tz.xml"
#t="iati-identifier/text() starts with reporting-org/@ref?"
#t="activity-date[@type='end-planned']/@iso-date or activity-date[@type='end-planned']/text() or activity-date[@type='end-actual']/@iso-date or activity-date[@type='end-actual']/text() or transaction-date/@iso-date (for any transaction[transaction-type/@code='D']|transaction[transaction-type/@code='E']) is less than 13 months ago?"
#t="conditions or document-link/category[@code='A04'] exists (if activity-status/@code is at least 2 and conditions/@attached is not 0)?"
#t="budget or planned-disbursement is available forward (if activity-status/@code is at least 2)?"
#t="budget or planned-disbursement is available forward by quarters (if activity-status/@code is at least 2)?"
#t="participating-org/@type is an integer?"
t="capital-spend exists (if activity-status/@code is at least 2 and (default-aid-type/@code or transaction/aid-type/@code is not A01 or A02))?"
test.test_doc(f,t)
