from ortools.linear_solver import pywraplp
import numpy as np 

def create_data_model(length):
    """Create the data for the example."""
    
    data = {}
    
    length = length * 4
    
    [1] * 5
    
    data['length'] = length
    data['items'] = list(range(len(length)))
    data['rod'] = data['items']
    data['rod_capacity'] = 12.05
    
    return data


def main(data):
    collect=[]

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver('SCIP')


    # Variables
    # x[i, j] = 1 if item i is cut in rod j.
    x = {}
    for i in data['items']:
        for j in data['rod']:
            x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))

    # y[j] = 1 if rod j is used.
    y = {}
    for j in data['rod']:
        y[j] = solver.IntVar(0, 1, 'y[%i]' % j)

    # Constraints
    # Each item must be in exactly one rod cut.
    for i in data['items']:
        solver.Add(sum(x[i, j] for j in data['rod']) >= 1)

    # The amount packed in each rod cannot exceed its capacity.
    for j in data['rod']:
        solver.Add(
            sum(x[(i, j)] * data['length'][i] for i in data['items']) <= y[j] *
            data['rod_capacity'])

    # Objective: minimize the number of rod used.
    solver.Minimize(solver.Sum([y[j] for j in data['rod']]))

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        num_rods = 0.
        for j in data['rod']:
            if y[j].solution_value() == 1:
                bin_items = []
                rod_length = []
                
                bin_weight = 0
                for i in data['items']:
                    if x[i, j].solution_value() > 0:
                        
                        
                        bin_items.append(i)
                        rod_length.append((data['length'][i]))
                        bin_weight += data['length'][i]
                     
                if bin_weight > 0:
                    num_rods += 1
                    #print('  Total length:', bin_weight/100)
                    #print('  Rod Len Cut: ',rod_length)
                    #print()
                    collect.append(rod_length)
        #print()
        #print('Number of rods used:', num_rods)
        #print('Time = ', solver.WallTime(), ' milliseconds')
    else:
        print('The problem does not have an optimal solution.')
    return collect


import pandas as pd

def get_combis(data):

    collect = main(data)

    df = pd.DataFrame(columns=['combination'])

    df['combination'] = collect

    df['combination'] = df.combination.apply(lambda x: np.sort(x))

    df['total_length'] = df['combination'].apply(lambda arr: sum(arr))

    df = df.sort_values(by=['total_length'], ascending = False).reset_index(drop=True)

    drop_index = []

    for index, row in df.iterrows():
        
        if index != (len(df) -1):
            
            if list(np.sort(row['combination'])) == list(np.sort(df.iloc[index+1]['combination'])):
                
                drop_index.append(index)
                
    df = df.drop(drop_index).reset_index(drop=True)
    
    return df


def get_beam_amount(demand,occurence):
    
    amount = int(demand/occurence)

    rest = demand%occurence
    
    pieces = amount * occurence
    
    return {'amount': amount,
           'rest': rest, 
           'pieces': pieces}
    
def get_max_values(combo, cust_dem):

    max_vals = pd.DataFrame(columns = list(dict.fromkeys(combo)))

    for pos in list(dict.fromkeys(combo)):
        
        demand = cust_dem.loc[cust_dem['length'] == pos]['open_qty'].values[0]
        
        beam_amount = get_beam_amount(demand,combo.count(pos))
        
        max_vals[pos] = [beam_amount['pieces'] / combo.count(pos)]
        
    return max_vals


def create_prd_orders(cust_dem):
    
    iterations = 500
    early_stopping = 5
    divider = 10
    
    production_orders = []

    while iterations > 0 and early_stopping > 0:
        
        prd_order = []
        
        iterations -= 1

        #############################################################

        data = create_data_model(cust_dem['length'].tolist())

        combos = get_combis(data)
        
        if len(combos) > 0:

            combo = combos.iloc[0]['combination'].tolist()
            prd_order.append(combo)
            combo_length = combos.iloc[0]['total_length']
            prd_order.append(combo_length)

            #############################################################

            max_vals = get_max_values(combo, cust_dem)

            amount = max_vals[max_vals.idxmin(axis=1)[0]].values[0]
            
            #amount = int(amount/divider) * divider
            
            if amount > 0:
                
                prd_order.append(amount)
            
                production_orders.append(prd_order)

                #print(amount)
                #print(combo)

                for pos in list(dict.fromkeys(combo)):
                    
                    #print(str(pos) + ' - ' + str((combo.count(pos) * amount)))
                    
                    open_qty = cust_dem.loc[cust_dem['length'] == pos]['open_qty'].values[0]
                    
                    open_qty_new = open_qty - (combo.count(pos) * amount)
                    
                    if int(open_qty_new) == 0:
                        
                        open_qty_new = None
                        
                    #print(open_qty_new)
                    
                    index = cust_dem.loc[cust_dem['length'] == pos].index[0]
                    
                    cust_dem.loc[index, 'open_qty'] = open_qty_new 
                    
                    cust_dem = cust_dem.dropna()
                    
            else:
                early_stopping -= 1
                
        else:
            early_stopping -= 1
            
    production_orders = pd.DataFrame(production_orders, columns=['combo','raw_length','amount'])
    
    return cust_dem.dropna().reset_index(drop=True), production_orders