from graphviz import Digraph

def create_atc_flowchart():
    dot = Digraph("ATC_Simulation_Flowchart")
    
    # Start Node
    dot.node("Start", "Start Simulation")
    
    # User Role Selection
    dot.node("Role", "Select Role (ATC / Ground Control)")
    dot.edge("Start", "Role")
    
    # ATC Branch
    dot.node("ATC_UI", "Load ATC Interface")
    dot.node("Monitor_Aircraft", "Monitor Aircraft Movements")
    dot.node("Check_Conflicts", "Check for Conflicts")
    dot.node("Issue_Commands", "Issue Commands to Aircraft")
    dot.node("Receive_Response", "Receive Pilot Response")
    dot.node("Update_Status", "Update Aircraft Status")
    
    dot.edge("Role", "ATC_UI", label="ATC Mode")
    dot.edge("ATC_UI", "Monitor_Aircraft")
    dot.edge("Monitor_Aircraft", "Check_Conflicts")
    dot.edge("Check_Conflicts", "Issue_Commands", label="If Conflict Detected")
    dot.edge("Issue_Commands", "Receive_Response")
    dot.edge("Receive_Response", "Update_Status")
    dot.edge("Update_Status", "Monitor_Aircraft")
    
    # Ground Control Branch
    dot.node("GC_UI", "Load Ground Control Interface")
    dot.node("Monitor_Ground", "Monitor Aircraft on Ground")
    dot.node("Assign_Taxiways", "Assign Taxiways & Runways")
    dot.node("GC_Commands", "Issue Taxiing & Clearance Commands")
    dot.node("Receive_Pilot_Response", "Receive Pilot Acknowledgment")
    dot.node("Update_Ground_Status", "Update Ground Movement Status")
    
    dot.edge("Role", "GC_UI", label="Ground Control Mode")
    dot.edge("GC_UI", "Monitor_Ground")
    dot.edge("Monitor_Ground", "Assign_Taxiways")
    dot.edge("Assign_Taxiways", "GC_Commands")
    dot.edge("GC_Commands", "Receive_Pilot_Response")
    dot.edge("Receive_Pilot_Response", "Update_Ground_Status")
    dot.edge("Update_Ground_Status", "Monitor_Ground")
    
    # End Condition
    dot.node("End", "Simulation Ends")
    dot.edge("Monitor_Aircraft", "End", label="Exit Condition Met")
    dot.edge("Monitor_Ground", "End", label="Exit Condition Met")
    
    return dot

# Generate and render the flowchart
dot = create_atc_flowchart()
dot.render("atc_simulation_flowchart", format="png", cleanup=False)
print("Flowchart generated and saved as atc_simulation_flowchart.png")
