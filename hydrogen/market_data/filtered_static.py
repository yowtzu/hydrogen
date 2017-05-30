import pandas as pd
from hydrogen.system import universe_filename, static_filename, filtered_static_filename

static = pd.read_csv(static_filename)
universe = pd.read_csv(universe_filename)
universe['CT_LIST'] = universe.CT_LIST.apply(list)

rows = []
universe.apply(lambda x: [ rows.append([x.GROUP, x.ROOT_TICKER, x.DESCRIPTION, month]) for month in x.CT_LIST  ], axis=1);
universe_long = pd.DataFrame(rows, columns=universe.columns)
universe_long["REGEX"] = [x[0] + y + '[0-9]+ ' + x[1] for x, y in zip(universe_long.ROOT_TICKER.str.split('1 '), universe_long.CT_LIST)]

regex = "(" + '|'.join(universe_long.REGEX) + ")"
filtered_static = static[static.TICKER.str.contains(regex)]
filtered_static.to_csv(filtered_static_filename, index=False)
