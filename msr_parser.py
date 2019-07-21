"""
msr_parser.py

Outline:
    A file parser for PayPal Monthly Sales Reports (MSR) files (CSV format).
    PayPal does not offer much to track subscriptions (churn, average length etc).
    This parser is part of a set of files developed to extract, process, analzye and
    visualize information about recurring subscriptions from PayPal MSR reports.

Author:
    Max Krichenbauer

License:
    GNU General Public License v3.0
    https://www.gnu.org/licenses/gpl-3.0.en.html
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
    THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
    PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
    EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
    PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR 
    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY 
    OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Example use:
    # Parse my PayPal MSR files:
    [subscriptions, months] = parse_msr_files('D:/myFiles/paypal/', reporting_currency='USD')
    # Report some stats:
    print("AVERAGE SUBSCRIPTION LENGTH: " + str(subscriptions['length'].mean()))
    print("AVERAGE SUBSCRIPTION GROSS: " + str(subscriptions['gross'].mean()))
    print("AVERAGE GROWTH RATE: " + str(months['growth'].mean()))
    print("AVERAGE CHURN RATE: " + str(months['churn'].mean()))
    # Save to CSV:
    subscriptions.to_csv(path_or_buf='D:/myFiles/subscriptions.csv', index=False)
    months.to_csv(path_or_buf='D:/myFiles/months.csv', index=False)

"""
import requests
import datetime
import pandas as pd
import os
import glob
import re

def parse_msr_files(folder,
                    filename_pattern='MSR-*.CSV', 
                    filename_year=[-10, -6], 
                    filename_month=[-6, -4],
                    reporting_currency=False,
                    print_stats=True):
    """
    Parse Paypal Monthly Sales Reports (MSR) CSV files and 
    extract data about the subscriptions reported in the files.
    It automatically converts currencies by using exchangeratesapi.io
    (using the dayly exchange rate reported on the day of the transaction).
    
    @param folder:  The folder in which to search for.
    @param filename_pattern: The pattern in which files are named.
                             Default is the PayPal format (eg. "MSR-201901.CSV")
    @param filename_year:    Where in the filename the year is specified (indices).
    @param filename_month:   Where in the filename the month is specified (indices).
    @param reporting_currency: In which currency to report gross / revenue.
                               If none is specified, the first detected currency
                               will be used.
    @param print_stats:      Whether to print out statistics for each parsed file.
    @return: Two Pandas data frames, the first one containing data per subscriptions
             and the second one containing data per month.
    """
    #
    # During parsing: collect data in a dictionary
    subscriptions = {}
    months = {}
    # Find MSR files in the folder
    infiles = glob.glob( os.path.join(folder, filename_pattern) )
    infiles.sort()
    #
    if print_stats:
        # Print title line
        print("Year: Month: Active: New: Cancel:   Growth: Churn:  Revenue:")
    for infile in infiles:
        prior_subscriptions = 0
        for subscription_id,subscription in subscriptions.items():
            if subscription['status'] == 'active':
                subscription['status'] = 'tentative'
                prior_subscriptions += 1
        # initialize accumulator variables
        active_subscriptions = 0
        new_subscriptions = 0
        monthly_revenue = 0
        # print("> Parsing file: " + infile)
        year = infile[filename_year[0] : filename_year[1]]
        month = infile[filename_month[0] : filename_month[1]]
        data = pd.read_csv(infile, header=0)
        # Available columns in PayPal MSR's:
        # "Date","Time","Time Zone","Description","Currency","Gross","Fee",
        # "Net","Balance","Transaction ID","From Email Address","Name",
        # "Bank Name","Bank Account","Shipping and Handling Amount",
        # "Sales Tax","Invoice ID","Reference Txn ID"
        # Many of these can be expected to be empty.
        # Usually, 'Reference Txn ID' is the subscription ID,
        # but this is not always the case. Therefore, we'll
        # try to match payments to known subscriptions in multiple ways.
        for index, row in data.iterrows():
            # For subscriptions, 'Description' should be 'Subscription Payment'
            if row['Description'] != 'Subscription Payment':
                continue
            #
            # Parse the data
            date = row['Date']
            if bool(re.match(r"[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}", date)):
                date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
            elif bool(re.match(r"[0-9]{1,2}-[0-9]{1,2}-[0-9]{4}", date)):
                date = datetime.datetime.strptime(date, '%m-%d-%Y').date()
            else:
                date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            gross = row['Gross']
            if type(gross) is str:
                gross = float(gross.replace(',',''))
            # Convert currency if needed
            currency = row['Currency']
            if reporting_currency == False:
                # reporting_currency was not yet defined, use this from now on
                reporting_currency = currency
            elif currency != reporting_currency:
                # convert currency using exchangeratesapi.io
                datestr = date.strftime("%Y-%m-%d")
                response = requests.get('https://api.exchangeratesapi.io/'+datestr+'?base='+reporting_currency+'&symbols='+currency)
                if response.status_code == 200:
                    xchange_rate = response.json()['rates'][currency]
                    gross = gross / float(xchange_rate)
            #
            # Try to match the subscription to one we know from previous files
            subscription = None
            for prior_subscription in subscriptions.values():
                if prior_subscription['status'] != 'tentative':
                    continue # only compare it to those subscriptions that were active last month
                if isinstance(row['Reference Txn ID'], str) and row['Reference Txn ID'] == prior_subscription['id']:
                    subscription = prior_subscription
                    break
                if row['From Email Address'] == prior_subscription['email']:
                    subscription = prior_subscription
                    break
            # ^ tried to mach the current row to an active subscription
            
            if subscription is None:
                # new subscription
                subscription_id = None
                if isinstance(row['Reference Txn ID'], str) and len(row['Reference Txn ID']) > 3 and row['Reference Txn ID'][1] == '-':
                    subscription_id = row['Reference Txn ID']
                else:
                    n = 1
                    while (row['From Email Address'] + "_" + str(n)) in subscriptions:
                        n += 1
                    subscription_id = (row['From Email Address'] + "_" + str(n))
                
                subscriptions[subscription_id] = {
                    'id': subscription_id,
                    'name': row['Name'],
                    'email': row['From Email Address'],
                    'start': date,
                    'end': date,
                    'length': 1,
                    'currency': reporting_currency,
                    'gross': gross,
                    'original_currency': row['Currency'],
                    'original_gross': row['Gross'],
                    'status': 'active'
                    }
                new_subscriptions += 1
                # print("NEW SUBCRIPTION:" + subscription_id)
            else: 
                # subscription was renewed, so push back the end-date
                subscription['end'] = date
                subscription['length'] += 1
                # sum up total amount spent
                subscription['gross'] += gross
                subscription['status'] = 'active'
                # print("SUBCRIPTION RENEWED:" + subscription['id'])
            # ^ adding new subscription or updating existing one
            active_subscriptions += 1
            monthly_revenue += gross
        # ^ iterated over all items in this month
        canceled_subscription = 0
        for subscription_id,subscription in subscriptions.items():
            if subscription['status'] == 'tentative':
                subscription['status'] = 'canceled'
                canceled_subscription += 1
        growth = 100
        churn = 0
        if prior_subscriptions != 0:
            growth = (100.0 * float(new_subscriptions) / float(prior_subscriptions))
            churn  = (100.0 * float(canceled_subscription) / float(prior_subscriptions))
        if print_stats:
            # "Year: Month: Active: New: Cancel: Growth: Churn: Revenue:"
            print(year+"  "
                +month+"     "
                +('%3i' % (active_subscriptions))+"     "
                +('%3i' % (new_subscriptions))+"  "
                +('%3i' % (canceled_subscription))+"     "
                +('%6.2f%%' % (growth)) + " "
                +('%6.2f%%' % (churn)) + " "
                +('%5i' % (monthly_revenue)) + " " + reporting_currency
                )
        # 
        month_id = year + "-" + month
        months[month_id] = {
            'id': month_id,
            'year': year,
            'month': month,
            'active_subscriptions': active_subscriptions,
            'new_subscriptions': new_subscriptions,
            'canceled_subscription': canceled_subscription,
            'growth': growth,
            'churn': churn,
            'revenue':monthly_revenue,
            'currency':reporting_currency
            }
        #
    # Convert to Pandas DataFrame for further processing
    subscriptions = pd.DataFrame(data=subscriptions).transpose()
    months = pd.DataFrame(data=months).transpose()
    return [subscriptions, months]
#
