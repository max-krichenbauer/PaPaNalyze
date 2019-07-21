# Parse my PayPal MSR files:
import msr_parser
import subscriptions_analyzer

[subscriptions, months] = msr_parser.parse_msr_files('D:/Dropbox/biz/paypal/', reporting_currency='USD')
# Analyze and plot results:
subscriptions_analyzer.plot_subscriptions(subscriptions, months)
