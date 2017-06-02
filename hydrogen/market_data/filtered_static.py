import pandas as pd
from hydrogen.system import universe_filename, static_filename, filtered_static_filename
import hydrogen.system as system

static = pd.read_csv(static_filename)
universe = pd.read_csv(universe_filename)
universe['CT_LIST'] = universe.CT_LIST.apply(list)

rows = []
universe.apply(lambda x: [ rows.append([x.GROUP, x.ROOT_TICKER, x.DESCRIPTION, month]) for month in x.CT_LIST  ], axis=1);
universe_long = pd.DataFrame(rows, columns=universe.columns)
universe_long["REGEX"] = [x[0] + y + '[0-9]+ ' + x[1] for x, y in zip(universe_long.ROOT_TICKER.str.split('1 '), universe_long.CT_LIST)]

regex = "(" + '|'.join(universe_long.REGEX) + ")"
filtered_static = static[static.TICKER.str.contains(regex)]

filtered_static["ROOT_TICKER"] = filtered_static.TICKER.str.replace('[A-Z][0-9]+', '1')
filtered_static
filtered_static = filtered_static.merge(universe, on='ROOT_TICKER')
filtered_static["MONTHS_BTW_CT"] = system.n_month_in_year/filtered_static.CT_LIST.apply(len)/12
filtered_static.drop('CT_LIST', axis=1, inplace=True)
filtered_static.to_csv(filtered_static_filename, index=False)
