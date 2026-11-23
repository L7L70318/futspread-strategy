"""Economically motivated seasonal calendar-spread whitelist (43 candidates)."""

SEASONAL_SPREADS = {
    # Natural gas: winter withdrawal, summer injection, and the Mar/Apr turn.
    'NG[H][J0]': ('natural_gas_storage', 'March/April withdrawal-to-injection transition'),
    'NG[J][X0]': ('natural_gas_storage', 'April/November injection-season span'),
    'NG[U][F0]': ('natural_gas_storage', 'September/January summer-to-winter transition'),
    'NG[V][F0]': ('natural_gas_storage', 'October/January pre-winter storage risk'),
    'NG[X][F0]': ('natural_gas_storage', 'November/January winter demand curve'),

    # Refined products and crude: heating and summer driving/refinery seasons.
    'HO[Q][F0]': ('heating_fuel', 'August/January pre-heating-season spread'),
    'HO[U][F0]': ('heating_fuel', 'September/January heating-season spread'),
    'HO[V][H0]': ('heating_fuel', 'October/March winter heating span'),
    'RB[G][M0]': ('gasoline_driving', 'February/June summer-grade and driving season'),
    'RB[J][M0]': ('gasoline_driving', 'April/June driving-season transition'),
    'RB[U][F0]': ('gasoline_driving', 'September/January summer-to-winter gasoline'),
    'CL[H][M0]': ('crude_refinery', 'March/June refinery and summer-demand transition'),
    'CL[U][Z0]': ('crude_refinery', 'September/December refinery-maintenance transition'),
    'BRN[H][M0]': ('crude_refinery', 'March/June global summer-demand transition'),
    'BRN[U][Z0]': ('crude_refinery', 'September/December refinery-demand transition'),
    'G[Q][F0]': ('heating_fuel', 'August/January European heating-oil season'),
    'G[V][H0]': ('heating_fuel', 'October/March European winter span'),

    # Corn/wheat: old crop, weather market, harvest, and new crop.
    'ZC[N][U0]': ('grain_crop_cycle', 'July/September old-to-new-crop transition'),
    'ZC[N][Z0]': ('grain_crop_cycle', 'July weather-market versus December new crop'),
    'ZC[U][Z0]': ('grain_crop_cycle', 'September/December harvest and new crop'),
    'ZW[H][N0]': ('grain_crop_cycle', 'March/July winter-wheat harvest span'),
    'ZW[K][N0]': ('grain_crop_cycle', 'May/July winter-wheat harvest transition'),
    'KE[H][N0]': ('grain_crop_cycle', 'March/July HRW harvest span'),
    'KE[K][N0]': ('grain_crop_cycle', 'May/July HRW harvest transition'),

    # Soy complex: July/August old crop versus autumn harvest/new crop.
    'ZS[N][X0]': ('soy_crop_cycle', 'July/November old-crop versus new-crop soybeans'),
    'ZS[Q][X0]': ('soy_crop_cycle', 'August/November soybean harvest transition'),
    'ZS[U][X0]': ('soy_crop_cycle', 'September/November soybean harvest'),
    'ZM[N][Z0]': ('soy_crop_cycle', 'July/December soybean-meal crop transition'),
    'ZM[U][Z0]': ('soy_crop_cycle', 'September/December soybean-meal harvest'),
    'ZL[N][Z0]': ('soy_crop_cycle', 'July/December soybean-oil crop transition'),
    'ZL[U][Z0]': ('soy_crop_cycle', 'September/December soybean-oil harvest'),

    # Livestock: biological production cycle and seasonal meat demand.
    'HE[J][M0]': ('hog_cycle', 'April/June approach to summer hog-price peak'),
    'HE[M][N0]': ('hog_cycle', 'June/July summer hog-price peak'),
    'HE[N][Q0]': ('hog_cycle', 'July/August post-peak transition'),
    'HE[Q][V0]': ('hog_cycle', 'August/October seasonal hog decline'),
    'HE[V][Z0]': ('hog_cycle', 'October/December autumn-to-winter hog cycle'),
    'LE[M][V0]': ('cattle_cycle', 'June/October fed-cattle seasonal transition'),
    'LE[Q][Z0]': ('cattle_cycle', 'August/December stronger year-end cattle demand'),
    'LE[V][Z0]': ('cattle_cycle', 'October/December year-end cattle strength'),
    'GF[Q][X0]': ('cattle_cycle', 'August/November feeder seasonal transition'),
    'GF[U][X0]': ('cattle_cycle', 'September/November feeder seasonal transition'),

    # Dairy: spring production flush and later-year demand/production balance.
    'DC[J][M0]': ('dairy_cycle', 'April/June spring milk-production flush'),
    'DC[M][V0]': ('dairy_cycle', 'June/October post-flush dairy transition'),
}

assert len(SEASONAL_SPREADS) == 43
