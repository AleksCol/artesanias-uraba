def formato_de_pesos(centavos: int) -> str:
    """Convierte centavos a pesos con el separador de miles colombiano.

    Los precios se guardan en centavos porque es lo que espera Stripe, pero
    en Colombia nadie escribe los centavos: 8000000 se muestra como $ 80.000.
    """
    return "$ " + f"{centavos // 100:,}".replace(",", ".")
