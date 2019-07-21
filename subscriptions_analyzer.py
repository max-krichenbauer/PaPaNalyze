"""
subscriptions_analyzer.py

Outline:
    Data analysis of PayPal subscription data extracted from PayPal
    monthly sales reports (MSRs).
    PayPal does not offer much to track subscriptions (churn, average length etc).
    This analyzer is part of a set of files developed to extract, process, analzye and
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
    import msr_parser
    [subscriptions, months] = msr_parser.parse_msr_files('D:/myFiles/paypal/', reporting_currency='USD')
    # Analyze and plot results:
    plot_subscriptions(subscriptions, months)
"""
import datetime
import pandas as pd
import numpy as np
import os
import math
import matplotlib as mpl
import matplotlib.pyplot as plt

def plot_subscriptions(subscriptions, months):
    """
    Analyze and plot PayPal subscription data.
    
    @param subscriptions:   Per-subscription data frame.
    @param months:          Per-month data frame.
    """
    currency = months.currency[0]
    
    indices = pd.RangeIndex(months.shape[0]) # np.arange(months.shape[0])
    months = months.set_index(indices)
    months.active_subscriptions = pd.to_numeric(months.active_subscriptions)
    months.revenue = pd.to_numeric(months.revenue)
    months.growth = pd.to_numeric(months.growth)
    months.churn = pd.to_numeric(months.churn)
    
    model_active_subscriptions = np.polyfit(months.index, months.active_subscriptions, 1)
    fit_active_subscriptions = (months.index * model_active_subscriptions[0]) + model_active_subscriptions[1]
    model_revenue = np.polyfit(months.index, months.revenue, 1)
    fit_revenue = (months.index * model_revenue[0]) + model_revenue[1]

    plt.subplot(2, 2, 1)
    plt.bar(months.id.values, months.active_subscriptions.values, label = "Active Subscriptions")
    plt.plot(months.id.values, fit_active_subscriptions, color='blue')
    plt.title('Active Subscriptions')
    plt.xticks(rotation='vertical')
    plt.ylabel('#')
    plt.ylim(ymin=0)

    plt.subplot(2, 2, 2)
    plt.plot(months.id.values, months.growth.values, label = "Growth")
    plt.plot(months.id.values, months.churn.values, label = "Churn")
    plt.title('Growth and Churn')
    plt.xticks(rotation='vertical')
    plt.ylabel('%')
    plt.legend()
    plt.ylim(ymin=0)

    plt.subplot(2, 2, 3)
    plt.bar(months.id.values, months.revenue.values, label = "Revenue")
    plt.plot(months.id.values, fit_revenue, color='blue')
    plt.title('Revenue')
    plt.xticks(rotation='vertical')
    plt.ylabel(currency)
    plt.ylim(ymin=0)

    average_subscription_duration = subscriptions['length'].mean()
    average_subscription_duration = ('%.2f' % (average_subscription_duration))
    average_subscription_duration = ("Average subscription duration: " + average_subscription_duration + " months")
    plt.figtext(0.50, 0.4, average_subscription_duration, horizontalalignment='left', verticalalignment='center')

    average_subscription_revenue = subscriptions['gross'].mean()
    average_subscription_revenue = ('%.2f' % (average_subscription_revenue))
    average_subscription_revenue = ("Average subscription revenue: " + average_subscription_revenue + " " + currency)
    plt.figtext(0.50, 0.35, average_subscription_revenue, horizontalalignment='left', verticalalignment='center')

    average_growth_rate = months['growth'].mean()
    average_growth_rate = ('%.2f' % (average_growth_rate))
    average_growth_rate = ("Average growth rate: " + average_growth_rate + " %")
    plt.figtext(0.50, 0.3, average_growth_rate, horizontalalignment='left', verticalalignment='center')

    average_churn_rate = months['churn'].mean()
    average_churn_rate = ('%.2f' % (average_churn_rate))
    average_churn_rate = ("Average churn rate: " + average_churn_rate + " %")
    plt.figtext(0.50, 0.25, average_churn_rate, horizontalalignment='left', verticalalignment='center')

    plt.subplots_adjust(hspace=0.85, bottom=0.2)
    plt.show()
#
