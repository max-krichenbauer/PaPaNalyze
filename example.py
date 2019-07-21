# Parse my PayPal MSR files:
import msr_parser
import subscriptions_analyzer

# Parse data from PayPal monthly sales reports (MSR) files:
[subscriptions, months] = msr_parser.parse_msr_files('C:/MSR files folder/', reporting_currency='USD')
# Analyze and plot results:
subscriptions_analyzer.plot_subscriptions(subscriptions, months)
