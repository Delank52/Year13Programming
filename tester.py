from datetime import date

# Define the weekly rates and the dates they started
rates = [
    (date(2008, 4, 19), date(2009, 4, 5), 18.80),
    (date(2009, 4, 6), date(2010, 4, 4), 20.00),
    (date(2010, 4, 5), date(2011, 4, 3), 20.30),
    (date(2011, 4, 4), date(2012, 4, 1), 20.30),
    (date(2012, 4, 2), date(2013, 4, 7), 20.30),
    (date(2013, 4, 8), date(2014, 4, 6), 20.30),
    (date(2014, 4, 7), date(2015, 4, 5), 20.50),
    (date(2015, 4, 6), date(2016, 4, 3), 20.70),
    (date(2016, 4, 4), date(2017, 4, 2), 20.70),
    (date(2017, 4, 3), date(2018, 4, 1), 20.70),
    (date(2018, 4, 2), date(2019, 4, 7), 20.70),
    (date(2019, 4, 8), date(2020, 4, 5), 20.70),
    (date(2020, 4, 6), date(2021, 4, 4), 21.05),
    (date(2021, 4, 5), date(2022, 4, 3), 21.15),
    (date(2022, 4, 4), date(2023, 4, 2), 21.80),
    (date(2023, 4, 3), date(2024, 4, 7), 24.00),
    (date(2024, 4, 8), date(2025, 4, 6), 25.60),
    (date(2025, 4, 7), date(2025, 6, 12), 26.05),
]

# Calculate total benefit
total_benefit = 0.0

for start, end, weekly_rate in rates:
    duration_days = (end - start).days
    weeks = duration_days / 7
    total_benefit += weeks * weekly_rate

print(f"Estimated total Child Benefit from 19 April 2008 to 12 June 2025: £{total_benefit:.2f}")
