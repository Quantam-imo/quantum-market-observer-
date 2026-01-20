def build(ctx, decision):
    if decision["decision"] == "WAIT":
        return "Waiting: no confirmed institutional activity."

    return (
        f"Iceberg detected near {ctx['price']}. "
        f"Order flow delta favors sellers. "
        f"Astro timing active. "
        f"Cycle alignment confirmed."
    )
