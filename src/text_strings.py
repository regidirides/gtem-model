"""Every user-facing string in the figures and the PDF report, in one place.

Centralised deliberately, so that adding a language never requires another
sweep through the plotting and report code.

WHAT IS TRANSLATED, AND WHAT IS NOT
    Translated: everything a person reads — figure titles, axis labels,
    legends, and the prose of the PDF report.

    NOT translated: anything a machine reads — configuration keys, CSV column
    headers, output file names, and the identifiers inside the model. Two runs
    of the same scenario must produce tables that can be compared column by
    column whatever language the report was written in. ``col_minutes`` and
    ``col_outcome`` below are CSV headers and are therefore identical in every
    table; ``test_text_strings.py`` enforces that.

ADDING A LANGUAGE
    Copy ``EN``, translate the values, leave the keys and the ``{placeholders}``
    exactly as they are, and register the result in ``TABLES``. The tests check
    that every table has the same keys and the same placeholders as ``EN``.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping

#: CSV column headers. Identical in every language, by design - see the module
#: docstring. Listed here so the tests can assert it rather than trust it.
#:
#: Naming convention: ``col_*`` is a CSV column header and is NEVER translated;
#: ``th_*`` is a heading of a table inside the PDF and always is.
UNTRANSLATED_KEYS = frozenset({"col_minutes", "col_outcome"})

#: Values that are legitimately identical in more than one language - numeric
#: formats and international words. Listed so that a genuinely forgotten
#: translation still fails ``test_translation_leaves_nothing_in_english``.
SAME_IN_EVERY_LANGUAGE = frozenset({
    "pdf_milestone_minutes",   # "{minutes:.1f} min"
    "pdf_extra_minutes",       # "+{minutes} min"
    "th_error",                # "Error"
})

EN: dict[str, str] = {
    # --- shared vocabulary -------------------------------------------------
    "safe_zone": "safe zone",
    "safe_zones": "safe zones",
    "minutes": "Minutes",
    "people": "People",
    "percent_of_population": "% of population",
    "speed_ms": "Speed (m/s)",
    "adults": "Adults",
    "elderly": "Elderly",
    "children": "Children",
    "all_groups": "All groups",

    # --- outcomes ----------------------------------------------------------
    "evacuated": "Evacuated before the tsunami",
    "not_evacuated": "NOT evacuated",
    "caught": "Caught in transit",
    "stranded": "Stranded (no route)",

    # --- figure 1: dynamics ------------------------------------------------
    "fig1_title": "Evacuation progress by age group",
    "fig1_suptitle": "Percentage of each group that has reached a safe zone",
    "fig1_xlabel": "Minutes since the earthquake",
    "fig1_ylabel": "% evacuated",
    "fig1_eta_label": "Tsunami arrives ({eta:g} min)",
    "fig1_after_eta": "After the wave",

    # --- figure 2: speeds --------------------------------------------------
    "fig2_title": "Walking speed by age group",
    "fig2_suptitle": "Mean speed of each group. Falls below free-flow where the "
                     "network is congested.",
    "fig2_free_flow": "Free-flow speed ({v:.2f} m/s)",

    # --- figure 3: vulnerability -------------------------------------------
    "fig3_title": "Evacuation vulnerability by starting location",
    "fig3_subtitle": "Where people started, coloured by how long they took. "
                     "Black = did not reach safety.",
    "fig3_legend_fast": "Reached safety < {low:g} min",
    "fig3_legend_mid": "Reached safety {low:g}-{high:g} min",
    "fig3_legend_slow": "Reached safety > {high:g} min",
    "fig3_legend_failed": "DID NOT reach safety",
    "fig3_no_data": "No vulnerability data recorded",

    # --- figure 4: safe-zone demand ----------------------------------------
    "fig4_title": "Demand on each safe zone",
    "fig4_subtitle": "Marker size and colour show how many people arrived. "
                     "The {n} that received people are labelled.",
    "fig4_people_received": "People received",
    "fig4_unused": "Received nobody",

    # --- figure 5: congestion ----------------------------------------------
    "fig5_title": "Street congestion, weighted by how long it lasted",
    "fig5_subtitle": "Criticality = accumulated crowding over time "
                     "(person-seconds per m2), not peak density alone.",
    "fig5_colorbar": "Accumulated crowding (person-s/m2)",
    "fig5_ranking": "Most critical stretches\n(accumulated crowding):",
    "fig5_rank_row": " #{rank} (nodes {a}-{b}): {value:.1f}",
    "fig5_no_data": "No congestion recorded",

    # --- CSV column headers -------------------------------------------------
    # Machine-readable. NOT translated - see UNTRANSLATED_KEYS.
    "col_minutes": "Time_Minutes",
    "col_outcome": "Outcome",

    # --- PDF ----------------------------------------------------------------
    "pdf_title": "Tsunami evacuation simulation report",
    "pdf_warnings_heading": "Input data warnings",
    "pdf_no_warnings": "No input warnings. Every input check passed.",
    "pdf_warnings_intro": "These issues were detected in the input data. They do "
                          "not stop the simulation, but they affect how much "
                          "confidence the results deserve.",
    "pdf_limitations": "What this model can and cannot tell you: see "
                       "docs/LIMITATIONS.md. In short, GTEM simulates pedestrians "
                       "only, assumes everyone knows the whole road network and "
                       "walks the shortest route, and does not re-route around "
                       "congestion.",

    # --- figure 1 panel headers ---------------------------------------------
    "fig1_panel": "{group} - {pct:.1f}% evacuated ({evacuated:,} of {total:,})",

    # --- PDF: cover and headline ---------------------------------------------
    "pdf_subtitle": "Area: {zone}   |   Seed: {seed}   |   {version}",
    "pdf_footer": "{provenance}  |  page {page}  |  generated {timestamp}",
    "pdf_headline_heading": "Headline result",
    "pdf_banner_evacuated": "{label} ({n:,} people)",
    "pdf_headline_some": "Of {requested:,} people simulated, {evacuated:,} reached "
                         "a safe zone before the tsunami arrived at {eta} minutes, "
                         "and {not_evacuated:,} did not. {breakdown} The three "
                         "outcomes always add up to the total - nobody is left out "
                         "of the count.",
    "pdf_headline_all": "Of {requested:,} people simulated, all {evacuated:,} "
                        "reached a safe zone before the tsunami arrived at {eta} "
                        "minutes. {breakdown} The three outcomes always add up to "
                        "the total - nobody is left out of the count.",
    "pdf_breakdown_none": "Everyone reached safety in time.",
    "pdf_breakdown_both": "Of those, {caught:,} were still walking when the wave "
                          "arrived and {stranded:,} had no route to any safe zone "
                          "from where they started.",
    "pdf_breakdown_stranded": "All {stranded:,} of them had no route to any safe "
                              "zone from where they started, so they could never "
                              "have reached safety on this network.",
    "pdf_breakdown_caught": "All of them were still walking when the wave arrived; "
                            "everyone had a route, but not enough time to use it.",

    # --- PDF: how the evacuation unfolded ------------------------------------
    # --- batch figures ------------------------------------------------------
    "conv_xlabel": "Number of replicates included (accumulated from run 1)",
    "conv_ylabel": "Coefficient of variation of {metric} (%)",
    "conv_title": "Convergence of the evacuation estimate\n"
                  "(converged = CV stays within {tolerance:.0%} of its final "
                  "value from that n onward)",
    "conv_summary_header": "# Convergence - {metric}",
    "conv_settles": "  CV settles at n = {n} (within {tolerance:.0%} of the "
                    "final CV, and stays)",
    "conv_not_reached": "not reached",
    "conv_achieved": "  95% CI half-width achieved = +/- {achieved:.3f} pp",
    "conv_needed": "  replicates needed for +/- {target} pp = {needed}",
    "bench_xlabel_nodes": "Network size (nodes)",
    "bench_xlabel_agents": "Agents created",
    "bench_ylabel": "Total runtime (s)",
    "bench_title_nodes": "Runtime vs network size",
    "bench_title_agents": "Runtime vs population",
    "pdf_warnings_untranslated": "The warnings below are produced by the "
                                "simulation engine and are only available in "
                                "English.",
    "pdf_config_untranslated": "Setting names are the column names of "
                               "Run_Summary.csv and are identical in every "
                               "language, so that a report and its data tables "
                               "can be read side by side.",
    "pdf_unfolded_heading": "How the evacuation unfolded",
    "pdf_unfolded_intro": "When each share of the population reached safety. A "
                          "late 25% mark points to slow departure; a late 90% "
                          "mark points to distance or congestion.",
    "pdf_milestone": "{share:.0%} of the population reached safety",
    "pdf_milestone_minutes": "{minutes:.1f} min",
    "pdf_milestone_never": "not reached before the wave",
    "pdf_flow_peak": "Fastest arrival rate",
    "pdf_flow_peak_value": "{rate:,.0f} people/min, at {minutes:.1f} min",
    "pdf_flow_tail": "Still arriving in the final minute",
    "pdf_flow_tail_value": "{rate:,.0f} people/min",

    # --- PDF: outcome by age group -------------------------------------------
    "pdf_ages_heading": "Outcome by age group",
    "pdf_ages_intro": "A group that lags the others needs different preparedness "
                      "measures, not simply more signage.",
    "th_group": "Group",
    "th_people": "People",
    "th_evacuated": "Evacuated",
    "th_not_evacuated": "Not evacuated",
    "th_evacuated_pct": "Evacuated %",

    # --- PDF: time margin ------------------------------------------------------
    "pdf_margin_heading": "How much time was missing",
    "pdf_margin_intro": "Repeating this scenario with no time limit, and the same "
                        "seed, everyone who had a route reached safety after "
                        "{required:.1f} minutes. The wave arrives at {eta:.1f} "
                        "minutes, so the shortfall is {deficit:.1f} minutes. The "
                        "table shows how many more people would have reached "
                        "safety for each extra minute of warning or earlier "
                        "departure.",
    "pdf_margin_note": "Extra time can come from a longer warning, or from people "
                       "leaving sooner. The model treats the two identically, so "
                       "this table is also a measure of what preparedness would "
                       "be worth.",
    "th_extra_time": "Extra time",
    "th_reached_safety": "Reached safety",
    "th_additional_people": "Additional people",
    "th_share_of_population": "Share of population",
    "pdf_extra_minutes": "+{minutes} min",

    # --- PDF: configuration ----------------------------------------------------
    "pdf_config_heading": "Run configuration (complete)",
    "pdf_config_intro": "Every setting used by this run. A run can be reproduced "
                        "exactly from this table plus the seed.",
    "label_area": "Area",
    "label_seed": "Seed",
    "label_version": "GTEM version",

    # --- PDF: safe zones and congestion ----------------------------------------
    "pdf_zones_heading": "Where people went",
    "pdf_zones_intro": "Demand on each safe zone, busiest first. A zone receiving "
                       "nobody may be unreachable, badly placed, or simply not "
                       "needed - check which before removing it from a plan.",
    "th_rank": "Rank",
    "th_safe_zone": "Safe zone",
    "th_name": "Name",
    "th_people_received": "People received",
    "pdf_congestion_heading": "Most critical street stretches",
    "pdf_congestion_intro": "Ranked by accumulated crowding (person-seconds per "
                            "square metre), which counts how long congestion "
                            "lasted, not only how bad it briefly got. These are "
                            "the stretches where widening, clearing or re-routing "
                            "would save the most time.",
    "th_from_node": "From node",
    "th_to_node": "To node",
    "th_accumulated_crowding": "Accumulated crowding",
    "th_peak_density": "Peak density",
    "th_seconds_congested": "Seconds congested",

    # --- PDF: figures and files -------------------------------------------------
    "pdf_figures_heading": "Figures and how to read them",
    "pdf_figure_missing": "FIGURE MISSING: {name} was not produced by this run. "
                          "This report is incomplete.",
    "pdf_files_heading": "Files produced by this run",

    # --- PDF: figure captions ----------------------------------------------------
    "cap_fig1_title": "Evacuation progress by age group",
    "cap_fig1": "How quickly each group reached safety. The red line is the "
                "tsunami arrival time: anything to the right of it did not happen "
                "in time. Compare the three panels - a group that lags behind "
                "needs different preparedness measures, not just more signage.",
    "cap_fig2_title": "Walking speed by age group",
    "cap_fig2": "Mean walking speed over time. Dips below the free-flow line mean "
                "people were held up by crowding. Sustained dips point to a "
                "capacity problem on the network, not to slow walkers.",
    "cap_fig3_title": "Vulnerability by starting location",
    "cap_fig3": "Where people started, coloured by how long they took to reach "
                "safety. BLACK POINTS DID NOT REACH SAFETY AT ALL. Black clusters "
                "are the priority areas: they show places where evacuation fails, "
                "not merely places where it is slow.",
    "cap_fig4_title": "Demand on each safe zone",
    "cap_fig4": "How many people arrived at each safe zone. Large uneven markers "
                "mean demand is concentrated: check that the busiest zones can "
                "physically hold and support the number shown, and that zones "
                "receiving nobody are reachable at all.",
    "cap_fig5_title": "Street congestion weighted by duration",
    "cap_fig5": "Criticality is accumulated crowding over time, not the single "
                "worst moment. A street that was briefly busy ranks below one "
                "that was moderately crowded for many minutes, which is the one "
                "that actually delays people.",

    # --- batch report --------------------------------------------------------------
    "batch_title": "Tsunami evacuation - batch report",
    "batch_subtitle": "{runs} successful run(s) across {scenarios} scenario(s)"
                      "   |   {version}",
    "batch_results_heading": "Results, averaged over replicates",
    "batch_results_intro": "Each row is a scenario, not a run. The spread is the "
                           "standard deviation across replicates: it is the amount "
                           "by which an answer would move if you happened to pick "
                           "a different random seed. Quote the mean with its "
                           "spread, never a single run.",
    "th_scenario": "Scenario",
    "th_runs": "Runs",
    "th_evacuated_mean": "Evacuated (mean +/- SD)",
    "th_not_evacuated_mean": "NOT evacuated (mean +/- SD)",
    "th_stranded": "Stranded",
    "th_difference": "Difference",
    "th_people_not_evacuated": "People not evacuated",
    "batch_baseline": "baseline",
    "batch_not_available": "n/a",
    "batch_compare_heading": "Comparing the scenarios",
    "batch_compare_intro": "'{best}' performs best, at {pct:.2f}% evacuated. The "
                           "differences below are what the comparison is for; "
                           "treat a difference smaller than the standard "
                           "deviations above as indistinguishable from seed noise.",
    "batch_size_heading": "Was this batch large enough?",
    "batch_size_intro": "Measured for each scenario from the accumulated "
                        "coefficient of variation:",
    "batch_size_unavailable": "Convergence could not be assessed: at least three "
                              "replicates per scenario are needed.",
    "batch_not_settled": "The estimate has NOT settled for: {scenarios}. Treat "
                         "those figures as provisional and run more replicates "
                         "before quoting them.",
    "batch_repro_heading": "Reproducibility and cost",
    "label_master_seed": "Master seed",
    "label_no_master_seed": "not set - this batch is NOT reproducible",
    "label_successful_runs": "Successful runs",
    "label_failed_runs": "Failed runs",
    "label_total_compute": "Total compute",
    "label_mean_per_run": "Mean per run",
    "label_timestep": "Timestep",
    "batch_no_seed_note": "Without a master seed this batch cannot be reproduced. "
                          "Pass --seed to make it repeatable.",
    "batch_failed_heading": "Failed runs",
    "th_run": "Run",
    "th_error": "Error",
    "batch_figures_heading": "Figures",
    "batch_limitations_heading": "What this batch cannot tell you",
    "cap_batch_convergence_title": "How many replicates the estimate needed",
    "cap_batch_convergence": "Coefficient of variation of the evacuation rate, "
                             "accumulated from run 1 onward. Where the curve "
                             "flattens, adding replicates stops changing the "
                             "answer. A curve still falling at the right-hand edge "
                             "means the batch was too small.",
    "cap_batch_runtime_title": "Runtime against problem size",
    "cap_batch_runtime": "How long a run takes as the network and population grow. "
                         "Useful for planning how large a study is affordable.",
}

# --- BEGIN TRANSLATED CONTENT ------------------------------------------------
# Everything to the END marker is Spanish ON PURPOSE, and is exempt from the
# English-only gate in tests/test_english_only.py. That gate exists to stop
# Spanish leaking back into identifiers, comments and code; it must keep
# applying to the whole of the rest of this file.

ES: dict[str, str] = {
    # --- vocabulario compartido --------------------------------------------
    "safe_zone": "zona segura",
    "safe_zones": "zonas seguras",
    "minutes": "Minutos",
    "people": "Personas",
    "percent_of_population": "% de la población",
    "speed_ms": "Velocidad (m/s)",
    "adults": "Adultos",
    "elderly": "Adultos mayores",
    "children": "Niños",
    "all_groups": "Todos los grupos",

    # --- resultados ---------------------------------------------------------
    "evacuated": "Evacuados antes del tsunami",
    "not_evacuated": "NO evacuados",
    "caught": "Sorprendidos en tránsito",
    "stranded": "Sin ruta de evacuación",

    # --- figura 1: dinámica -------------------------------------------------
    "fig1_title": "Avance de la evacuación por grupo de edad",
    "fig1_suptitle": "Porcentaje de cada grupo que ha llegado a una zona segura",
    "fig1_xlabel": "Minutos desde el sismo",
    "fig1_ylabel": "% evacuado",
    "fig1_eta_label": "Llegada del tsunami ({eta:g} min)",
    "fig1_after_eta": "Después de la ola",

    # --- figura 2: velocidades ----------------------------------------------
    "fig2_title": "Velocidad de caminata por grupo de edad",
    "fig2_suptitle": "Velocidad media de cada grupo. Cae por debajo del flujo "
                     "libre donde la red está congestionada.",
    "fig2_free_flow": "Velocidad de flujo libre ({v:.2f} m/s)",

    # --- figura 3: vulnerabilidad -------------------------------------------
    "fig3_title": "Vulnerabilidad de evacuación según el punto de partida",
    "fig3_subtitle": "Dónde partió cada persona, coloreado según cuánto tardó. "
                     "Negro = no llegó a una zona segura.",
    "fig3_legend_fast": "Llegó a zona segura en < {low:g} min",
    "fig3_legend_mid": "Llegó a zona segura en {low:g}-{high:g} min",
    "fig3_legend_slow": "Llegó a zona segura en > {high:g} min",
    "fig3_legend_failed": "NO llegó a zona segura",
    "fig3_no_data": "No se registraron datos de vulnerabilidad",

    # --- figura 4: demanda sobre las zonas seguras --------------------------
    "fig4_title": "Demanda sobre cada zona segura",
    "fig4_subtitle": "El tamaño y el color del marcador indican cuántas personas "
                     "llegaron. Se rotulan las {n} que recibieron personas.",
    "fig4_people_received": "Personas recibidas",
    "fig4_unused": "No recibió a nadie",

    # --- figura 5: congestión -----------------------------------------------
    "fig5_title": "Congestión de las calles, ponderada por su duración",
    "fig5_subtitle": "Criticidad = aglomeración acumulada en el tiempo "
                     "(persona-segundo por m2), no solo la densidad máxima.",
    "fig5_colorbar": "Aglomeración acumulada (persona-s/m2)",
    "fig5_ranking": "Tramos más críticos\n(aglomeración acumulada):",
    "fig5_rank_row": " #{rank} (nodos {a}-{b}): {value:.1f}",
    "fig5_no_data": "No se registró congestión",

    # --- encabezados de columna CSV ------------------------------------------
    # Legibles por máquina. NO se traducen - ver UNTRANSLATED_KEYS.
    "col_minutes": "Time_Minutes",
    "col_outcome": "Outcome",

    # --- PDF ------------------------------------------------------------------
    "pdf_title": "Informe de simulación de evacuación ante tsunami",
    "pdf_warnings_heading": "Advertencias sobre los datos de entrada",
    "pdf_no_warnings": "Sin advertencias. Los datos de entrada superaron todas "
                       "las verificaciones.",
    "pdf_warnings_intro": "Se detectaron estos problemas en los datos de entrada. "
                          "No impiden la simulación, pero afectan la confianza "
                          "que merecen los resultados.",
    "pdf_limitations": "Lo que este modelo puede y no puede decirle: ver "
                       "docs/LIMITATIONS.md. En resumen, GTEM simula únicamente "
                       "peatones, supone que todos conocen la red vial completa y "
                       "caminan por la ruta más corta, y no recalculan la ruta "
                       "para esquivar la congestión.",

    # --- figura 1: encabezados de panel --------------------------------------
    "fig1_panel": "{group} - {pct:.1f}% evacuado ({evacuated:,} de {total:,})",

    # --- PDF: portada y resultado principal ----------------------------------
    "pdf_subtitle": "Área: {zone}   |   Semilla: {seed}   |   {version}",
    "pdf_footer": "{provenance}  |  página {page}  |  generado {timestamp}",
    "pdf_headline_heading": "Resultado principal",
    "pdf_banner_evacuated": "{label} ({n:,} personas)",
    "pdf_headline_some": "De {requested:,} personas simuladas, {evacuated:,} "
                         "llegaron a una zona segura antes de que el tsunami "
                         "arribara a los {eta} minutos, y {not_evacuated:,} no lo "
                         "lograron. {breakdown} Los tres resultados siempre suman "
                         "el total: nadie queda fuera del recuento.",
    "pdf_headline_all": "De {requested:,} personas simuladas, las {evacuated:,} "
                        "llegaron a una zona segura antes de que el tsunami "
                        "arribara a los {eta} minutos. {breakdown} Los tres "
                        "resultados siempre suman el total: nadie queda fuera del "
                        "recuento.",
    "pdf_breakdown_none": "Todos llegaron a un lugar seguro a tiempo.",
    "pdf_breakdown_both": "De ellos, {caught:,} seguían caminando cuando llegó la "
                          "ola y {stranded:,} no tenían ninguna ruta hacia una "
                          "zona segura desde donde partieron.",
    "pdf_breakdown_stranded": "Las {stranded:,} personas no tenían ninguna ruta "
                              "hacia una zona segura desde donde partieron, de "
                              "modo que nunca habrían podido ponerse a salvo en "
                              "esta red vial.",
    "pdf_breakdown_caught": "Todas seguían caminando cuando llegó la ola: tenían "
                            "ruta, pero no tiempo suficiente para recorrerla.",

    # --- PDF: cómo se desarrolló la evacuación --------------------------------
    # --- figuras del lote -----------------------------------------------------
    "conv_xlabel": "Cantidad de réplicas incluidas (acumuladas desde la corrida 1)",
    "conv_ylabel": "Coeficiente de variación de {metric} (%)",
    "conv_title": "Convergencia de la estimación de evacuación\n"
                  "(convergida = el CV se mantiene dentro del {tolerance:.0%} de "
                  "su valor final desde esa n en adelante)",
    "conv_summary_header": "# Convergencia - {metric}",
    "conv_settles": "  El CV se estabiliza en n = {n} (dentro del {tolerance:.0%} "
                    "del CV final, y se mantiene)",
    "conv_not_reached": "no alcanzado",
    "conv_achieved": "  Semiamplitud del IC 95% alcanzada = +/- {achieved:.3f} pp",
    "conv_needed": "  réplicas necesarias para +/- {target} pp = {needed}",
    "bench_xlabel_nodes": "Tamaño de la red (nodos)",
    "bench_xlabel_agents": "Agentes creados",
    "bench_ylabel": "Tiempo total de ejecución (s)",
    "bench_title_nodes": "Tiempo de ejecución según el tamaño de la red",
    "bench_title_agents": "Tiempo de ejecución según la población",
    "pdf_warnings_untranslated": "Las advertencias siguientes son generadas por "
                                "el motor de simulación y solo están disponibles "
                                "en inglés.",
    "pdf_config_untranslated": "Los nombres de los parámetros son los "
                               "encabezados de columna de Run_Summary.csv y son "
                               "idénticos en todos los idiomas, para que el "
                               "informe y sus tablas de datos puedan leerse en "
                               "paralelo.",
    "pdf_unfolded_heading": "Cómo se desarrolló la evacuación",
    "pdf_unfolded_intro": "Momento en que cada porción de la población llegó a un "
                          "lugar seguro. Un 25% tardío indica salida lenta; un 90% "
                          "tardío indica distancia o congestión.",
    "pdf_milestone": "{share:.0%} de la población llegó a un lugar seguro",
    "pdf_milestone_minutes": "{minutes:.1f} min",
    "pdf_milestone_never": "no se alcanzó antes de la ola",
    "pdf_flow_peak": "Tasa máxima de llegada",
    "pdf_flow_peak_value": "{rate:,.0f} personas/min, a los {minutes:.1f} min",
    "pdf_flow_tail": "Aún llegando en el último minuto",
    "pdf_flow_tail_value": "{rate:,.0f} personas/min",

    # --- PDF: resultado por grupo de edad -------------------------------------
    "pdf_ages_heading": "Resultado por grupo de edad",
    "pdf_ages_intro": "Un grupo que se rezaga respecto de los demás requiere "
                      "medidas de preparación distintas, no simplemente más "
                      "señalización.",
    "th_group": "Grupo",
    "th_people": "Personas",
    "th_evacuated": "Evacuadas",
    "th_not_evacuated": "No evacuadas",
    "th_evacuated_pct": "% evacuado",

    # --- PDF: margen de tiempo --------------------------------------------------
    "pdf_margin_heading": "Cuánto tiempo faltó",
    "pdf_margin_intro": "Al repetir este escenario sin límite de tiempo y con la "
                        "misma semilla, todas las personas con ruta llegaron a un "
                        "lugar seguro a los {required:.1f} minutos. La ola arriba "
                        "a los {eta:.1f} minutos, de modo que el déficit es de "
                        "{deficit:.1f} minutos. La tabla muestra cuántas personas "
                        "más habrían llegado a un lugar seguro por cada minuto "
                        "adicional de alerta o de salida anticipada.",
    "pdf_margin_note": "El tiempo adicional puede provenir de una alerta más "
                       "temprana o de que la gente salga antes. El modelo trata "
                       "ambos casos por igual, de modo que esta tabla también "
                       "mide cuánto valdría la preparación.",
    "th_extra_time": "Tiempo adicional",
    "th_reached_safety": "Llegaron a lugar seguro",
    "th_additional_people": "Personas adicionales",
    "th_share_of_population": "Porcentaje de la población",
    "pdf_extra_minutes": "+{minutes} min",

    # --- PDF: configuración -----------------------------------------------------
    "pdf_config_heading": "Configuración de la corrida (completa)",
    "pdf_config_intro": "Todos los valores usados en esta corrida. La corrida "
                        "puede reproducirse exactamente con esta tabla más la "
                        "semilla.",
    "label_area": "Área",
    "label_seed": "Semilla",
    "label_version": "Versión de GTEM",

    # --- PDF: zonas seguras y congestión -----------------------------------------
    "pdf_zones_heading": "Adónde fue la gente",
    "pdf_zones_intro": "Demanda sobre cada zona segura, de mayor a menor. Una zona "
                       "que no recibe a nadie puede ser inaccesible, estar mal "
                       "ubicada o simplemente no ser necesaria: conviene "
                       "averiguar cuál antes de retirarla de un plan.",
    "th_rank": "Puesto",
    "th_safe_zone": "Zona segura",
    "th_name": "Nombre",
    "th_people_received": "Personas recibidas",
    "pdf_congestion_heading": "Tramos de calle más críticos",
    "pdf_congestion_intro": "Ordenados por aglomeración acumulada (persona-segundo "
                            "por metro cuadrado), que mide cuánto duró la "
                            "congestión y no solo cuán intensa fue por un "
                            "instante. Son los tramos donde ensanchar, despejar o "
                            "desviar ahorraría más tiempo.",
    "th_from_node": "Nodo inicial",
    "th_to_node": "Nodo final",
    "th_accumulated_crowding": "Aglomeración acumulada",
    "th_peak_density": "Densidad máxima",
    "th_seconds_congested": "Segundos congestionado",

    # --- PDF: figuras y archivos --------------------------------------------------
    "pdf_figures_heading": "Figuras y cómo leerlas",
    "pdf_figure_missing": "FALTA LA FIGURA: esta corrida no generó {name}. Este "
                          "informe está incompleto.",
    "pdf_files_heading": "Archivos generados por esta corrida",

    # --- PDF: leyendas de las figuras ----------------------------------------------
    "cap_fig1_title": "Avance de la evacuación por grupo de edad",
    "cap_fig1": "Con qué rapidez llegó cada grupo a un lugar seguro. La línea roja "
                "es la hora de llegada del tsunami: nada de lo que está a su "
                "derecha ocurrió a tiempo. Compare los tres paneles: un grupo "
                "rezagado necesita medidas de preparación distintas, no solo más "
                "señalización.",
    "cap_fig2_title": "Velocidad de caminata por grupo de edad",
    "cap_fig2": "Velocidad media de caminata en el tiempo. Las caídas por debajo "
                "de la línea de flujo libre indican que la gente fue retenida por "
                "la aglomeración. Las caídas sostenidas señalan un problema de "
                "capacidad de la red, no personas que caminen lento.",
    "cap_fig3_title": "Vulnerabilidad según el punto de partida",
    "cap_fig3": "Dónde partió cada persona, coloreado según cuánto tardó en llegar "
                "a un lugar seguro. LOS PUNTOS NEGROS NUNCA LLEGARON A UN LUGAR "
                "SEGURO. Los grupos de puntos negros son las áreas prioritarias: "
                "muestran dónde la evacuación fracasa, no solo dónde es lenta.",
    "cap_fig4_title": "Demanda sobre cada zona segura",
    "cap_fig4": "Cuántas personas llegaron a cada zona segura. Marcadores grandes "
                "y desiguales indican demanda concentrada: verifique que las "
                "zonas más cargadas puedan albergar y atender físicamente la "
                "cantidad indicada, y que las que no reciben a nadie sean "
                "accesibles.",
    "cap_fig5_title": "Congestión de calles ponderada por su duración",
    "cap_fig5": "La criticidad es la aglomeración acumulada en el tiempo, no el "
                "peor instante. Una calle brevemente concurrida queda por debajo "
                "de otra moderadamente congestionada durante muchos minutos, que "
                "es la que en realidad demora a la gente.",

    # --- informe del lote -------------------------------------------------------------
    "batch_title": "Evacuación ante tsunami - informe del lote",
    "batch_subtitle": "{runs} corrida(s) exitosa(s) en {scenarios} escenario(s)"
                      "   |   {version}",
    "batch_results_heading": "Resultados promediados sobre las réplicas",
    "batch_results_intro": "Cada fila es un escenario, no una corrida. La "
                           "dispersión es la desviación estándar entre réplicas: "
                           "es cuánto se movería la respuesta si tocara otra "
                           "semilla aleatoria. Informe el promedio con su "
                           "dispersión, nunca una sola corrida.",
    "th_scenario": "Escenario",
    "th_runs": "Corridas",
    "th_evacuated_mean": "Evacuado (promedio +/- DE)",
    "th_not_evacuated_mean": "NO evacuado (promedio +/- DE)",
    "th_stranded": "Sin ruta",
    "th_difference": "Diferencia",
    "th_people_not_evacuated": "Personas no evacuadas",
    "batch_baseline": "referencia",
    "batch_not_available": "s/d",
    "batch_compare_heading": "Comparación de los escenarios",
    "batch_compare_intro": "'{best}' es el mejor, con {pct:.2f}% evacuado. Las "
                           "diferencias siguientes son el objeto de la "
                           "comparación; considere indistinguible del ruido de la "
                           "semilla toda diferencia menor que las desviaciones "
                           "estándar anteriores.",
    "batch_size_heading": "¿Fue suficientemente grande este lote?",
    "batch_size_intro": "Evaluado para cada escenario a partir del coeficiente de "
                        "variación acumulado:",
    "batch_size_unavailable": "No se pudo evaluar la convergencia: se necesitan al "
                              "menos tres réplicas por escenario.",
    "batch_not_settled": "La estimación NO se ha estabilizado para: {scenarios}. "
                         "Considere esas cifras provisionales y ejecute más "
                         "réplicas antes de citarlas.",
    "batch_repro_heading": "Reproducibilidad y costo",
    "label_master_seed": "Semilla maestra",
    "label_no_master_seed": "sin definir: este lote NO es reproducible",
    "label_successful_runs": "Corridas exitosas",
    "label_failed_runs": "Corridas fallidas",
    "label_total_compute": "Cómputo total",
    "label_mean_per_run": "Promedio por corrida",
    "label_timestep": "Paso de tiempo",
    "batch_no_seed_note": "Sin una semilla maestra este lote no puede "
                          "reproducirse. Use --seed para hacerlo repetible.",
    "batch_failed_heading": "Corridas fallidas",
    "th_run": "Corrida",
    "th_error": "Error",
    "batch_figures_heading": "Figuras",
    "batch_limitations_heading": "Lo que este lote no puede decirle",
    "cap_batch_convergence_title": "Cuántas réplicas necesitó la estimación",
    "cap_batch_convergence": "Coeficiente de variación de la tasa de evacuación, "
                             "acumulado desde la corrida 1. Donde la curva se "
                             "aplana, agregar réplicas deja de cambiar la "
                             "respuesta. Una curva que aún cae en el extremo "
                             "derecho significa que el lote fue demasiado "
                             "pequeño.",
    "cap_batch_runtime_title": "Tiempo de ejecución según el tamaño del problema",
    "cap_batch_runtime": "Cuánto tarda una corrida a medida que crecen la red y la "
                         "población. Útil para planificar qué tamaño de estudio "
                         "es viable.",
}

#: Every available table, keyed by the code used in the config file.
TABLES: dict[str, dict[str, str]] = {"en": EN, "es": ES}

#: Longer names accepted in the config file, for readability.
_ALIASES = {
    "english": "en", "ingles": "en", "inglés": "en",
    "spanish": "es", "espanol": "es", "español": "es", "castellano": "es",
}
# --- END TRANSLATED CONTENT --------------------------------------------------

#: Outcome codes written by the model into the vulnerability record.
OUTCOME_EVACUATED = 1
OUTCOME_CAUGHT = 2
OUTCOME_STRANDED = 3


def normalise_language(language: str) -> str:
    """Map a user-supplied language name to a table code, or raise."""
    key = str(language).strip().lower()
    key = _ALIASES.get(key, key)
    if key not in TABLES:
        raise ValueError(
            f"No string table for language {language!r}. "
            f"Available: {', '.join(sorted(TABLES))}. "
            "To add one, copy EN in src/text_strings.py, translate the values, "
            "and register it in TABLES."
        )
    return key


def strings(language: str = "en") -> dict[str, str]:
    """Return the string table for a language."""
    return TABLES[normalise_language(language)]


_active: dict[str, str] = EN


def set_language(language: str) -> str:
    """Select the language used by the figures and the report.

    Called once per run, before anything is drawn. Returns the resolved code.
    """
    global _active
    code = normalise_language(language)
    _active = TABLES[code]
    return code


def active_language() -> str:
    """The code of the currently selected language."""
    return next(code for code, table in TABLES.items() if table is _active)


class _ActiveTable(Mapping):
    """A live view of the selected table.

    ``figures.py`` and ``pdf_report.py`` bind this once at import time, so
    ``set_language`` takes effect without either module re-importing anything.
    A plain ``dict`` snapshot would freeze whichever language happened to be
    active when the module was first imported.
    """

    def __getitem__(self, key: str) -> str:
        return _active[key]

    def __iter__(self) -> Iterator[str]:
        return iter(_active)

    def __len__(self) -> int:
        return len(_active)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<active string table: {active_language()}>"


#: Import this, not a specific table, to follow the selected language.
ACTIVE = _ActiveTable()
