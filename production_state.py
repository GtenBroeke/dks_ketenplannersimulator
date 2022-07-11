
# production
OPVOERNORM  = 840       # parcels per gross hour per person

# limiting factors on gross production
REJECT      = 0.0500
OVERLOOP    = 0.0100
VALIDATE    = 0.0300

# production states per depot
MIN_STATE   = 2
MAX_STATE   = 10

# coefficients for personnel calculation, based on: y = ax + b; with x=production state
a           = 5
b           = 4

# ---------------------------
def get_productions_states(limiting_factors=REJECT + OVERLOOP + VALIDATE):

    # declare the dict
    production_dict = dict()

    # calculate production dict
    for state in range(MIN_STATE, MAX_STATE+1):
        production_dict[state] = {
            'production': int(state * OPVOERNORM * (1 - limiting_factors)),
            'medewerkers': int(a * state + b),
        }

    return production_dict