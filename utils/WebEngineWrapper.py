import plotly.graph_objects as go

def sunburst_chart_generic(data_raw, hierarchy_columns, value_column="montant", color_column=None, root_name="Total", negative_value_treatment=None):
    """
    Generates a Sunburst chart from raw data with a customizable hierarchy.

    Args:
        data_raw (list of dict): The input data, where each dictionary represents a row.
                                 Expected to have 'montant' and other columns specified in hierarchy_columns.
        hierarchy_columns (list of str): A list of column names defining the hierarchy
                                         from the outermost ring to the innermost.
                                         Example: ["type_flux", "compte", "categorie", "sous_cat"]
        value_column (str): The name of the column containing the numerical values for aggregation.
                            Defaults to "montant".
        color_column (str, optional): The name of the column to use for coloring the top-level segments.
                                      If None, default colors (red/green for negative/positive) are used.
                                      If specified, all segments will use the same color.
        root_name (str): The label for the center of the sunburst chart. Defaults to "Total".
        negative_value_treatment (dict, optional): A dictionary specifying how to handle negative values.
                                                   Expected keys:
                                                       "column_to_update": (str) The column whose value should be updated (e.g., "type_flux").
                                                       "negative_label": (str) The label to assign if the original value is negative.
                                                       "positive_label": (str) The label to assign if the original value is positive.
                                                   If None, negative values are treated as absolute and assigned a default 'Dépenses' type.
                                                   Example: {"column_to_update": "type_flux", "negative_label": "Dépenses", "positive_label": "Revenus"}
    Returns:
        plotly.graph_objects.Figure: A Plotly Sunburst chart figure.
    """

    processed_data = []
    for entry in data_raw:
        new_entry = entry.copy()
        # Handle negative values based on configuration
        if negative_value_treatment:
            if new_entry[value_column] < 0:
                new_entry[negative_value_treatment["column_to_update"]] = negative_value_treatment["negative_label"]
                new_entry[value_column] = round(abs(new_entry[value_column]), 2)
            else:
                new_entry[negative_value_treatment["column_to_update"]] = negative_value_treatment["positive_label"]
                new_entry[value_column] = round(new_entry[value_column], 2)
        else: # Default behavior if no specific treatment is provided
            if new_entry[value_column] < 0:
                new_entry["type_flux"] = "Dépenses" # This assumes 'type_flux' is a valid column if not specified in hierarchy_columns
                new_entry[value_column] = round(abs(new_entry[value_column]), 2)
            else:
                new_entry["type_flux"] = "Revenus" # This assumes 'type_flux' is a valid column
                new_entry[value_column] = round(new_entry[value_column], 2)

        processed_data.append(new_entry)

    # --- Construction des listes pour le Sunburst ---
    sunburst_labels = []
    sunburst_parents = []
    sunburst_values = []
    sunburst_ids = []
    sunburst_colors = []

    # Dictionnaire pour agréger les totaux par ID unique
    aggregated_totals = {}
    added_ids_to_sunburst_lists = set()

    # Define colors
    COLOR_DEFAULT_NEGATIVE = 'rgb(255, 99, 71)'  # Tomate (red)
    COLOR_DEFAULT_POSITIVE = 'rgb(60, 179, 113)' # Vert moyen

    # IDS Splitter
    var_split = "##"

    # Step 1: Process leaf nodes and accumulate totals for all levels
    for entry in processed_data:
        current_path_components = []
        parent_id = ""
        current_id = ""
        montant = round(entry[value_column], 2)

        for i, col in enumerate(hierarchy_columns):
            component = str(entry[col]) # Ensure component is string
            current_path_components.append(component)
            current_id = var_split.join(current_path_components)

            aggregated_totals[current_id] = aggregated_totals.get(current_id, 0) + montant

            if i == len(hierarchy_columns) - 1:  # This is the leaf node
                if current_id not in added_ids_to_sunburst_lists:
                    sunburst_ids.append(current_id)
                    # For leaf nodes, include value in label
                    sunburst_labels.append(f"{component} ({montant}€)")
                    sunburst_parents.append(parent_id if parent_id else root_name)
                    sunburst_values.append(montant)

                    # Determine color
                    if color_column and color_column in entry:
                        sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if entry[color_column] == negative_value_treatment["negative_label"] else COLOR_DEFAULT_POSITIVE)
                    elif negative_value_treatment and negative_value_treatment["column_to_update"] in entry:
                         sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if entry[negative_value_treatment["column_to_update"]] == negative_value_treatment["negative_label"] else COLOR_DEFAULT_POSITIVE)
                    else: # Fallback if no specific color column or negative treatment is provided
                        sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if entry[value_column] < 0 else COLOR_DEFAULT_POSITIVE)
                    
                    added_ids_to_sunburst_lists.add(current_id)
            
            parent_id = current_id

    # Step 2: Add intermediate and root nodes
    # Iterate in reverse order of hierarchy columns to ensure parents are added before children
    for i in range(len(hierarchy_columns) - 1, -1, -1):
        col = hierarchy_columns[i]
        unique_combinations = set()

        for entry in processed_data:
            current_path_components = []
            for j in range(i + 1): # Get components up to the current level
                current_path_components.append(str(entry[hierarchy_columns[j]]))
            unique_combinations.add(tuple(current_path_components))

        for combo in unique_combinations:
            current_id = var_split.join(combo)

            if current_id not in added_ids_to_sunburst_lists:
                sunburst_ids.append(current_id)
                sunburst_labels.append(combo[-1]) # Label is the last component of the path
                
                parent_id = ""
                if len(combo) > 1:
                    parent_id = var_split.join(combo[:-1])
                else:
                    parent_id = root_name # Top-level items parent to the root

                sunburst_parents.append(parent_id)
                sunburst_values.append(aggregated_totals.get(current_id, 0))

                # Determine color based on the top-most level of the hierarchy
                # This assumes the first column in hierarchy_columns is for coloring if no color_column is specified
                if color_column and color_column in entry:
                    # Find the corresponding original entry to get the color_column value
                    original_entry_for_color = next((item for item in processed_data if var_split.join([str(item[c]) for c in hierarchy_columns[:len(combo)]]) == current_id), None)
                    if original_entry_for_color:
                        sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if original_entry_for_color[color_column] == negative_value_treatment["negative_label"] else COLOR_DEFAULT_POSITIVE)
                    else:
                        sunburst_colors.append(COLOR_DEFAULT_POSITIVE) # Fallback
                elif negative_value_treatment and negative_value_treatment["column_to_update"] in entry:
                     # Find the corresponding original entry to get the negative_value_treatment["column_to_update"] value
                    original_entry_for_color = next((item for item in processed_data if var_split.join([str(item[c]) for c in hierarchy_columns[:len(combo)]]) == current_id), None)
                    if original_entry_for_color:
                        sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if original_entry_for_color[negative_value_treatment["column_to_update"]] == negative_value_treatment["negative_label"] else COLOR_DEFAULT_POSITIVE)
                    else:
                        sunburst_colors.append(COLOR_DEFAULT_POSITIVE) # Fallback
                else:
                    # Fallback to general negative/positive coloring based on aggregated value
                    sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if aggregated_totals.get(current_id, 0) < 0 else COLOR_DEFAULT_POSITIVE)

                added_ids_to_sunburst_lists.add(current_id)

    # Add the root node
    if root_name not in added_ids_to_sunburst_lists:
        sunburst_ids.append(root_name)
        sunburst_labels.append(root_name)
        sunburst_parents.append("")
        sunburst_values.append(sum(v for k, v in aggregated_totals.items() if len(k.split(var_split)) == 1)) # Sum of top-level aggregated values
        sunburst_colors.append('rgb(128, 128, 128)') # Neutral color for the root
        added_ids_to_sunburst_lists.add(root_name)

    # Note: custom_data handling for last_ring_values might need to be re-evaluated
    # as its purpose is not entirely clear from the original function and depends on downstream usage.
    # For now, let's simplify it or remove if not critical.
    # The original compte_ids logic is also specific and needs to be genericized or removed.
    # For now, let's make custom_data simpler or omit it if not crucial for the core chart.
    # custom_data = list(zip(last_ring_values, compte_ids)) # Original logic, needs re-evaluation for genericity

    # --- Création du graphique Sunburst ---
    fig = go.Figure(go.Sunburst(
        ids=sunburst_ids,
        labels=sunburst_labels,
        parents=sunburst_parents,
        values=sunburst_values,
        # customdata=custom_data, # Re-enable if you define generic custom_data
        branchvalues="total",
        hovertemplate='<b>%{label}</b><br>Montant: %{value}€<extra></extra>',
        marker=dict(colors=sunburst_colors)
    ))

    fig.update_layout(
        title="Sunburst Chart", # Generic title
        height=1200,
        width=1200,
        margin=dict(t=30, l=0, r=0, b=0)
    )

    return fig


data = [
    {"compte_id": "c1", "type_flux": "Dépenses", "compte": "Compte A", "categorie": "Logement", "sous_cat": "Loyer", "montant": 1200},
    {"compte_id": "c2", "type_flux": "Dépenses", "compte": "Compte A", "categorie": "Logement", "sous_cat": "Électricité", "montant": 80},
    {"compte_id": "c3", "type_flux": "Dépenses", "compte": "Compte B", "categorie": "Transport", "sous_cat": "Essence", "montant": 60},
    {"compte_id": "c4", "type_flux": "Revenus", "compte": "Compte C", "categorie": "Salaire", "sous_cat": "Principal", "montant": -2500}, # Negative for 'Revenus'
    {"compte_id": "c5", "type_flux": "Revenus", "compte": "Compte C", "categorie": "Investissements", "sous_cat": "Dividendes", "montant": -150},
    {"compte_id": "c6", "type_flux": "Dépenses", "compte": "Compte B", "categorie": "Alimentation", "sous_cat": "Courses", "montant": 300},
    {"compte_id": "c7", "type_flux": "Dépenses", "compte": "Compte A", "categorie": "Loisirs", "sous_cat": "Cinéma", "montant": 25},
    {"compte_id": "c8", "type_flux": "Dépenses", "compte": "Compte A", "categorie": "Loisirs", "sous_cat": "Restaurant", "montant": 75},
    {"compte_id": "c9", "type_flux": "Revenus", "compte": "Compte C", "categorie": "Salaire", "sous_cat": "Bonus", "montant": -500},
]

# Example 1: Original hierarchy with inferred type_flux from negative values
hierarchy_level_1 = ["type_flux", "compte", "categorie", "sous_cat"]
negative_treatment_1 = {
    "column_to_update": "type_flux",
    "negative_label": "Dépenses",
    "positive_label": "Revenus"
}
fig1 = sunburst_chart_generic(
    data_raw=data,
    hierarchy_columns=hierarchy_level_1,
    negative_value_treatment=negative_treatment_1,
    root_name="Global Financial Overview"
)
fig1.show()

# Example 2: A different hierarchy with fewer levels, and no specific negative value treatment (will use default)
data_less_levels = [
    {"Region": "North", "City": "New York", "Product": "Laptop", "Sales": 1000},
    {"Region": "North", "City": "New York", "Product": "Mouse", "Sales": 50},
    {"Region": "South", "City": "Miami", "Product": "Keyboard", "Sales": 200},
    {"Region": "South", "City": "Miami", "Product": "Laptop", "Sales": 1500},
    {"Region": "West", "City": "LA", "Product": "Monitor", "Sales": 700},
]
hierarchy_level_2 = ["Region", "City", "Product"]
fig2 = sunburst_chart_generic(
    data_raw=data_less_levels,
    hierarchy_columns=hierarchy_level_2,
    value_column="Sales",
    root_name="Total Sales"
)
fig2.show()

# Example 3: Hierarchy with only two levels and custom coloring based on 'Region' (if 'Region' were to be passed as a color_column)
data_simple = [
    {"Department": "HR", "Employee": "Alice", "Salary": 60000},
    {"Department": "HR", "Employee": "Bob", "Salary": 70000},
    {"Department": "Engineering", "Employee": "Charlie", "Salary": 100000},
    {"Department": "Engineering", "Employee": "David", "Salary": 95000},
]
hierarchy_level_3 = ["Department", "Employee"]
fig3 = sunburst_chart_generic(
    data_raw=data_simple,
    hierarchy_columns=hierarchy_level_3,
    value_column="Salary",
    root_name="Company Salaries"
)
fig3.show()