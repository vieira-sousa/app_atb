#!/usr/bin/env python3
"""
Builds data/protocols.json from the 7 ULS São João protocols in docs/protocols/.

Every clinical string below is transcribed verbatim (PT-PT) from the source PDFs.
Each node / regimen carries a `source` reference (section, page, figure/table).
Items whose source is ambiguous or internally contradictory carry an `issues`
list pointing to the IDs documented in CLINICAL_AUDIT.md.

Engine contract (consumed by the Phase 2 frontend):
  protocol.start             -> id of first node
  node.type == "question"    -> options[] each with `next` node id
  node.type == "result"      -> terminal recommendation
  result item `when`         -> {questionId: optionId | [optionIds]}; the item is shown
                                only if every listed question was answered with one of
                                the listed options (AND across keys).
  protocol.allergyQuestion   -> asked after reaching a result with antibiotherapy=true;
                                if "sim", the `allergy` regimens become primary.

Run:  python3 tools/build_protocols.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "protocols.json"


def src(section, page, element=None):
    d = {"section": section, "page": page}
    if element:
        d["element"] = element
    return d


def drug(name, dose=None, route=None, interval=None, note=None):
    d = {"drug": name, "dose": dose, "route": route, "interval": interval}
    if note:
        d["note"] = note
    return d


def regimen(verbatim, drugs, source, label=None, when=None, issues=None):
    r = {"verbatim": verbatim, "drugs": drugs, "source": source}
    if label:
        r["label"] = label
    if when:
        r["when"] = when
    if issues:
        r["issues"] = issues
    return r


def note(text, source, when=None, issues=None, kind="info"):
    n = {"kind": kind, "text": text, "source": source}
    if when:
        n["when"] = when
    if issues:
        n["issues"] = issues
    return n


# ---------------------------------------------------------------------------
# Shared definitions (verbatim per protocol; wording differs slightly between PDFs)
# ---------------------------------------------------------------------------
MDR_STD = [
    "Colonização conhecida por agentes multirresistentes no último ano;",
    "Exposição a antibioterapia nos últimos 3 meses;",
    "Infeção adquirida em ambiente hospitalar (doentes internados há mais de 48 horas);",
    "Doente institucionalizado ou internado nos últimos 3 meses.",
]

MDR_BILIARY = [
    "Exposição a antibioterapia nos últimos três meses;",
    "Infeção adquirida em ambiente hospitalar (doentes internados há mais de 48 horas);",
    "Presença de prótese na via biliar;",
    "Colonização conhecida por agentes multirresistentes (nestes casos, sempre que possível, discutir com a equipa do Programa de Apoio à Prescrição de Antibióticos o melhor esquema de antibioterapia).",
]

YES_NO = lambda yes_next, no_next, yes_crumb, no_crumb: [  # noqa: E731
    {"id": "sim", "label": "Sim", "next": yes_next, "crumb": yes_crumb},
    {"id": "nao", "label": "Não", "next": no_next, "crumb": no_crumb},
]

protocols = []

# ===========================================================================
# PAC176 — Apendicite aguda
# ===========================================================================
P176_GRAV = [
    "Pressão arterial média ≤60 mmHg",
    "Frequência cardíaca ≥100 bpm",
    "Frequência respiratória ≥22 cpm",
    "Alteração do estado de consciência",
    "Oligúria ou outra disfunção orgânica",
]
p176_allergy_nonmr = regimen(
    "Se alergia com indicação para evicção de β-lactâmicos: ciprofloxacina 400mg /8h + metronidazol 500 mg /8h",
    [drug("Ciprofloxacina", "400 mg", None, "8/8h"), drug("Metronidazol", "500 mg", None, "8/8h")],
    src("Figura 1 — Fluxograma de antibioterapia recomendado na AA", 8, "Caixa 'Fatores de risco para MR? — Não'"),
    issues=["B3"],
)
p176_allergy_mr = regimen(
    "Se alergia com indicação para evicção de β-lactâmicos: ciprofloxacina 400mg/8h + tigeciclina (100 mg e depois 50 mg /12h)",
    [drug("Ciprofloxacina", "400 mg", None, "8/8h"),
     drug("Tigeciclina", "100 mg (dose inicial) e depois 50 mg", None, "12/12h")],
    src("Figura 1 — Fluxograma de antibioterapia recomendado na AA", 8, "Caixa 'Fatores de risco para MR? — Sim'"),
    issues=["B3"],
)
p176_common = [
    note("As doses de antibioterapia devem ser ajustadas à função renal.", src("6.2.4", 6), kind="renal"),
    note("Está indicada a colheita de hemoculturas e de líquido intra-peritoneal para exame microbiológico em doentes instáveis clinicamente, em infeções adquiridas em ambiente hospitalar e se existirem fatores de risco para microrganismos multirresistentes. Duas hemoculturas (duas punções em locais diferentes; de cada punção 10 mL para frasco de aerobiose e 10 mL para frasco de anaerobiose), sempre antes da toma do antimicrobiano. Líquido intra-peritoneal para recipiente estéril e enviar para cultura (solicitar recipientes apropriados para anaeróbios).",
         src("6.2 Produtos a colher para estudo microbiológico", 5), kind="microbiology"),
    note("Se houver isolamento microbiológico em hemoculturas ou no líquido peritoneal aspirado aquando da cirurgia, a antibioterapia deve ser ajustada ao agente isolado e sempre tendo em conta os princípios de utilização dos antibióticos com menor espectro e toxicidade.",
         src("6.3 Tratamento antimicrobiano dirigido", 6), kind="deescalation"),
    note("Perante controlo de foco bem-sucedido e evolução clínica favorável, a transição para antibioterapia oral deve ocorrer o mais precocemente possível, idealmente ajustado ao isolamento. Em doentes sem critérios de sépsis e sem fatores de mau prognóstico e sem isolamento microbiológico pode ser considerado completar o tratamento via oral com cefixime 400mg/dia + metronidazol 500mg 8/8h.",
         src("6.4 Transição antibioterapia oral", 6), kind="oral"),
    note("Tendo em conta a boa biodisponibilidade deste antibiótico, o metronidazol caso esteja a ser utilizado por via endovenosa, deve assim que possível passar para administração por via oral.",
         src("6.5 Duração da antibioterapia", 7), kind="oral"),
    note("No caso de evolução desfavorável, ponderar reavaliação de controlo de foco com recurso a MCDTs dirigidos, devendo a duração de antibioterapia nestes casos ser definida caso a caso. Em determinadas situações, nomeadamente abcesso intra-abdominal em quadros com semanas de evolução, pode apenas estar indicada a drenagem percutânea associada a antibioterapia, devendo esta ser mantida até controlo adequado de foco.",
         src("6.5 Duração da antibioterapia", 7), kind="source_control"),
]
p176_dur_surg = [
    note("Apendicite aguda complicada: 96h após a cirurgia, se controlo de foco adequado.",
         src("6.5 Duração da antibioterapia — 2) Abordagem terapêutica com cirurgia + antibioterapia", 7),
         when={"q_indicacao": "complicada"}, kind="duration"),
    note("Duração não definida no protocolo para doença não complicada com FR para doença complicada ou com dúvida sobre controlo de foco (o protocolo refere apenas: 'Apendicite aguda não complicada: sem necessidade, se controlo de foco adequado').",
         src("6.5 Duração da antibioterapia", 7), when={"q_indicacao": ["fr", "duvida"]}, issues=["B5"], kind="duration"),
]

protocols.append({
    "id": "apendicite",
    "code": "ULSSJ-PAC176-0",
    "title": "Abordagem terapêutica da apendicite aguda",
    "titleEn": "Acute appendicitis",
    "sourceFile": "docs/protocols/ULSSJ-PAC176-0 Abordagem terapeutica da apendicite aguda.pdf",
    "edition": "Março 2026",
    "approved": "27/03/2026",
    "scope": "É aplicável aos doentes adultos com confirmação clínica e/ou imagiológica de AA.",
    "keywords": ["apendicite", "apendicectomia", "AA", "appendicitis"],
    "definitions": {
        "mdr": {"label": "Fatores de risco para infeções por agentes multirresistentes (MR)", "items": MDR_STD,
                "source": src("6.2 Seleção da antibioterapia empírica; Figura 1", 5)},
        "gravidade": {"label": "Critérios de gravidade", "items": P176_GRAV,
                      "source": src("Figura 1 (nota); Tabela 4 nota b", 8)},
        "fr_complicada": {"label": "FR doença complicada", "items": ["Apendicolito", ">70 anos (texto: 'Idade avançada')", "Gravidez", "Imunossupressão"],
                          "source": src("Figura 1 (nota); Tabela 4", 8), "issues": ["m4"]},
        "complicada": {"label": "Apendicite complicada", "items": ["Presença de gangrena, abcesso, perfuração e/ou peritonite generalizada"],
                       "source": src("Tabela 4 nota a", 4)},
    },
    "allergyQuestion": {"prompt": "Alergia com indicação para evicção de β-lactâmicos?", "source": src("Figura 1", 8)},
    "intro": [
        note("Tabela 4 — Complicada e/ou instabilidade clínica: Cirurgia + Antibioterapia. Não complicada com fatores de risco para doença complicada (apendicolito, idade avançada, gravidez, imunossupressão): Cirurgia +/- Antibioterapia. Não complicada, localizada e sem fatores de risco: Antibioterapia exclusiva ou Cirurgia +/- Antibioterapia.",
             src("6.1 Abordagem terapêutica — Tabela 4", 4)),
    ],
    "start": "q_abordagem",
    "nodes": {
        "q_abordagem": {
            "type": "question",
            "prompt": "Abordagem terapêutica",
            "help": "* Decisão de antibioterapia exclusiva deve ter em consideração a taxa aumentada de recorrência e internamentos potencialmente mais prolongados. Antibioterapia exclusiva poderá ser uma opção se o doente não tiver condições cirúrgicas.",
            "definitionRefs": ["complicada", "fr_complicada"],
            "options": [
                {"id": "cirurgia", "label": "Apendicectomia", "next": "q_indicacao", "crumb": "Apendicectomia"},
                {"id": "exclusiva", "label": "Antibioterapia exclusiva (sem cirurgia)", "next": "r_exclusiva", "crumb": "Antibioterapia exclusiva"},
            ],
            "source": src("Figura 1; Tabela 4", 8),
        },
        "q_indicacao": {
            "type": "question",
            "prompt": "Doença complicada / FR para doença complicada / dúvida se controlo de foco?",
            "definitionRefs": ["complicada", "fr_complicada"],
            "options": [
                {"id": "complicada", "label": "Doença complicada", "next": "q_mr", "crumb": "Complicada"},
                {"id": "fr", "label": "FR para doença complicada", "next": "q_mr", "crumb": "FR doença complicada"},
                {"id": "duvida", "label": "Dúvida se controlo de foco", "next": "q_mr", "crumb": "Dúvida controlo de foco"},
                {"id": "nao", "label": "Não (nenhum dos anteriores)", "next": "r_sem_atb", "crumb": "Não complicada, sem FR"},
            ],
            "source": src("Figura 1", 8, "Losango 'Doença complicada/FR para doença complicada/dúvida se controlo de foco?'"),
        },
        "q_mr": {
            "type": "question",
            "prompt": "Fatores de risco para MR?",
            "definitionRefs": ["mdr"],
            "options": YES_NO("q_gravidade", "r_ceftriaxone", "FR MR", "Sem FR MR"),
            "source": src("Figura 1", 8, "Losango 'Fatores de risco para MR?'"),
        },
        "q_gravidade": {
            "type": "question",
            "prompt": "Critérios de gravidade?",
            "definitionRefs": ["gravidade"],
            "options": YES_NO("r_meropenem", "r_piptazo", "Com critérios de gravidade", "Sem critérios de gravidade"),
            "source": src("Figura 1; 6.2.2; 6.2.3", 8),
        },
        "r_sem_atb": {
            "type": "result",
            "antibiotherapy": False,
            "title": "Sem necessidade de antibioterapia se controlo de foco adequado",
            "duration": [note("Apendicite aguda não complicada: sem necessidade, se controlo de foco adequado.",
                              src("6.5 Duração da antibioterapia", 7), kind="duration")],
            "notes": p176_common[1:2] + p176_common[5:],
            "source": [src("Figura 1", 8, "Caixa 'Sem necessidade de antibioterapia se controlo de foco adequado'")],
        },
        "r_ceftriaxone": {
            "type": "result",
            "antibiotherapy": True,
            "title": "Apendicite — sem FR para MR (independentemente da gravidade)",
            "firstLine": [regimen("Ceftriaxone 2g EV id + metronidazol 500mg EV q8h",
                                  [drug("Ceftriaxone", "2 g", "EV", "id"), drug("Metronidazol", "500 mg", "EV", "q8h")],
                                  src("6.2.1; Figura 1", 5))],
            "allergy": [p176_allergy_nonmr],
            "duration": p176_dur_surg,
            "notes": p176_common,
            "source": [src("6.2.1", 5), src("Figura 1", 8)],
        },
        "r_piptazo": {
            "type": "result",
            "antibiotherapy": True,
            "title": "Apendicite — FR para MR, sem critérios de gravidade",
            "firstLine": [regimen("Piperacilina/tazobactam 4.5g EV q6h",
                                  [drug("Piperacilina/tazobactam", "4,5 g", "EV", "q6h")], src("6.2.2; Figura 1", 5))],
            "alternatives": [
                regimen("Cefepime 2g EV q8h + Metronidazol 500mg EV q8h",
                        [drug("Cefepime", "2 g", "EV", "q8h"), drug("Metronidazol", "500 mg", "EV", "q8h")],
                        src("6.2.2", 6), issues=["B5"]),
                regimen("Ertapenem 1g EV id (se colonização por Enterobacteriaceae ESBL+)",
                        [drug("Ertapenem", "1 g", "EV", "id")], src("6.2.2", 6),
                        label="Se colonização por Enterobacteriaceae ESBL+", issues=["B5"]),
            ],
            "allergy": [p176_allergy_mr],
            "duration": p176_dur_surg,
            "notes": p176_common,
            "source": [src("6.2.2", 5), src("Figura 1", 8)],
        },
        "r_meropenem": {
            "type": "result",
            "antibiotherapy": True,
            "title": "Apendicite — FR para MR, com critérios de gravidade",
            "firstLine": [regimen("Meropenem 2g EV q8h",
                                  [drug("Meropenem", "2 g", "EV", "q8h")], src("6.2.3; Figura 1", 6))],
            "allergy": [p176_allergy_mr],
            "duration": p176_dur_surg,
            "notes": p176_common,
            "source": [src("6.2.3", 6), src("Figura 1", 8)],
            "issues": ["m6"],
        },
        "r_exclusiva": {
            "type": "result",
            "antibiotherapy": True,
            "pending": True,
            "title": "Antibioterapia exclusiva (sem cirurgia)",
            "firstLine": [],
            "duration": [note("Antibioterapia EV durante 48-72h seguida de 7-10 dias de antibioterapia oral.",
                              src("6.5 Duração da antibioterapia — 1) Abordagem terapêutica sem cirurgia", 6), kind="duration")],
            "notes": [
                note("O protocolo não define um esquema antibiótico específico para a estratégia de antibioterapia exclusiva.",
                     src("6.1; 6.2; 6.5", 4), issues=["B4"], kind="warning"),
                note("A decisão de antibioterapia exclusiva deve ter em consideração a taxa aumentada de recorrência de doença, cerca de 23-27% em 1 ano, e internamentos potencialmente mais prolongados, pelo que deverá ser ponderada cuidadosamente. Apesar da idade avançada ser um fator de risco para doença complicada, a antibioterapia exclusiva poderá ser uma opção se o doente não tiver condições cirúrgicas.",
                     src("6.1 Abordagem terapêutica", 4), kind="warning"),
            ] + p176_common,
            "source": [src("6.1; Tabela 4", 4), src("6.5", 6)],
            "issues": ["B4"],
        },
    },
})

# ===========================================================================
# PAC178 — Diverticulite aguda
# ===========================================================================
p178_allergy = lambda mdr: regimen(  # noqa: E731
    "Alergia a beta-lactâmicos: Ciprofloxacina 400mg 12/12h (se FR MDR: 8/8h) EV + Metronidazol 500mg 8/8h EV",
    [drug("Ciprofloxacina", "400 mg", "EV", "8/8h" if mdr else "12/12h"), drug("Metronidazol", "500 mg", "EV", "8/8h")],
    src("Figura 1. Abordagem terapêutica da Diverticulite Aguda", 6, "Caixa 'Alergia a beta-lactâmicos'"),
    issues=["m1"],
)
p178_complicated_interventions = [
    note("Considerar: Drenagem se abcesso > 5cm; Cirurgia se ar distante a > 5 cm do segmento inflamado ou evidência de peritonite.",
         src("Figura 1", 6, "Caixa 'Considerar'"), when={"q_complicada": "sim"}, kind="source_control", issues=["m2"]),
    note("Tabela 2 — Bolhas de ar pericólicas ou pouco líquido pericólico sem abscesso < 5 cm do segmento inflamado: cirurgia/drenagem Não. Abcesso < 4-5 cm: Não. Abcesso > 5 cm: Drenagem. Ar distante > 5 cm do segmento inflamado sem líquido livre: Considerar cirurgia. Líquido difuso na cavidade abdominal: Cirurgia.",
         src("6.1 — Tabela 2", 3), when={"q_complicada": "sim"}, kind="source_control", issues=["m2"]),
]
p178_common = [
    note("Recomenda-se a colheita dos seguintes produtos biológicos para microbiologia, se possível antes de iniciar antibioterapia, em todos os doentes clinicamente instáveis, em infeções adquiridas em ambiente hospitalar ou se existirem fatores de risco para microrganismos multirresistentes: dois sets de hemoculturas (duas punções em locais diferentes, 20 ml de sangue em cada punção, divididos em frascos de aerobiose e anaerobiose); líquido peritoneal (recipientes apropriados para anaeróbios), colhido de forma invasiva (intra-operatoriamente ou através de paracentese). Caso haja necessidade de repetir colheita, não deve ser colhido líquido peritoneal de drenos colocados há mais de 24h.",
         src("6.2 Produtos a colher para estudo microbiológico", 4), kind="microbiology"),
    note("Se houver isolamento microbiológico em hemoculturas ou no líquido peritoneal aspirado aquando da cirurgia, a antibioterapia deve ser ajustada ao agente isolado e sempre tendo em conta os princípios de utilização dos antibióticos com menor espectro e toxicidade.",
         src("6.4 Tratamento antimicrobiano dirigido", 7), kind="deescalation"),
    note("Os doentes que apresentem melhoria sustentada (normalização de parâmetros vitais e melhoria de parâmetros inflamatórios, melhoria de dor abdominal intensa, tolerância de dieta oral, existência de antibioterapia oral eficaz para os isolamentos microbiológicos e garantia de adesão à terapêutica em ambulatório), podem completar o curso de antibioterapia por via oral (ajustado ao isolamento microbiológico, ou discutir individualmente) no internamento ou em ambulatório. O metronidazol, caso esteja a ser utilizado por via endovenosa, deve assim que possível passar para administração por via oral.",
         src("6.3 Seleção da antibioterapia (p. 7)", 7), kind="oral"),
    note("Se evolução clínica indolente, considerar reavaliação imagiológica para exclusão de complicações que indiquem ou prolongamento de antibioterapia ou nova cirurgia.",
         src("6.5 Duração da antibioterapia", 7), kind="source_control"),
]
p178_duration = [
    note("Na generalidade dos doentes com diverticulite aguda, caso seja necessária antibioterapia, recomenda-se uma duração terapêutica de pelo [menos] 5 a 7 dias, podendo o curso ser completado por via oral sempre que os critérios de transição sejam cumpridos.",
         src("6.5 Duração da antibioterapia", 7), kind="duration", issues=["m3"]),
    note("Caso haja controlo de foco adequado (por abordagem cirúrgica ou drenagem percutânea), a antibioterapia pode ser suspensa 4 dias após a intervenção.",
         src("6.5 Duração da antibioterapia", 7), kind="duration"),
    note("No caso de existência de abcesso sem possibilidade de drenagem ou abordagem cirúrgica, o caso deve ter uma abordagem individualizada, de acordo com evolução clínica e imagiológica.",
         src("6.5 Duração da antibioterapia", 7), kind="duration"),
]
protocols.append({
    "id": "diverticulite",
    "code": "ULSSJ-PAC178-0",
    "title": "Abordagem farmacológica da diverticulite aguda",
    "titleEn": "Acute diverticulitis",
    "sourceFile": "docs/protocols/ULSSJ-PAC178-0 Abordagem farmacologica da diverticulite aguda.pdf",
    "edition": "Março 2026",
    "approved": "27/03/2026",
    "scope": "É aplicável aos doentes adultos com manifestações clínicas características e com confirmação imagiológica de DA.",
    "keywords": ["diverticulite", "DA", "sigmoide", "diverticulitis"],
    "definitions": {
        "mdr": {"label": "Fatores de risco para infeções por agentes multirresistentes (MDR)", "items": MDR_STD,
                "source": src("Figura 1, nota 1; 6.3", 5)},
        "wses": {"label": "Classificação WSES (TC) — Tabela 1", "items": [
            "Não complicada: Divertículos, espessamento da parede do cólon ou aumento da densidade da gordura pericólica",
            "Complicada 1a: Bolhas de ar pericólicas ou pouco líquido pericólico sem abscesso (distância <5 cm da inflamação do segmento intestinal)",
            "Complicada 1b: Abcesso <4cm",
            "Complicada 2a: Abcesso >4cm",
            "Complicada 2b: Ar distante (>5 cm do segmento intestinal inflamado)",
            "Complicada 3: Líquido peritoneal difuso sem ar livre distante (sem orifício no cólon)",
            "Complicada 4: Líquido peritoneal difuso com ar livre distante (orifício persistente no cólon)",
        ], "source": src("Tabela 1", 2)},
        "imunossupressao": {"label": "Imunossupressão", "items": [
            "Doentes sob corticoterapia ou outros imunossupressores, imunodeficiência primária, SIDA, neoplasia sob quimioterapia, diabetes mellitus com mau controlo metabólico"],
            "source": src("6.1 nota de rodapé 1", 3)},
        "sepsis": {"label": "Sépsis", "items": ["Infeção associada a disfunção orgânica potencialmente ameaçadora de vida"],
                   "source": src("6.1 nota de rodapé 2", 3)},
        "gravidade": {"label": "Gravidade clínica", "items": ["Sepsis", "Instabilidade hemodinâmica"],
                      "source": src("Figura 1", 6)},
    },
    "allergyQuestion": {"prompt": "Alergia a beta-lactâmicos?", "source": src("Figura 1", 6)},
    "intro": [
        note("Terapêutica de suporte: Fluidoterapia; Analgesia; Dieta zero / líquida, a progredir de acordo com tolerância.",
             src("Figura 1", 6, "Caixa inicial")),
    ],
    "start": "q_complicada",
    "nodes": {
        "q_complicada": {
            "type": "question",
            "prompt": "Evidência imagiológica de diverticulite aguda complicada?",
            "definitionRefs": ["wses"],
            "options": YES_NO("q_mdr", "q_fr_naocomplicada", "DA complicada", "DA não complicada"),
            "source": src("Figura 1", 6),
        },
        "q_fr_naocomplicada": {
            "type": "question",
            "prompt": "Fatores de risco para doença complicada?",
            "help": "Figura 1 apresenta apenas 'Imunosupressão?'. Tabela 2 e texto (6.1) incluem também Sépsis/Choque Séptico.",
            "definitionRefs": ["imunossupressao", "sepsis"],
            "options": [
                {"id": "imuno", "label": "Imunossupressão", "next": "q_mdr", "crumb": "Imunossupressão"},
                {"id": "sepsis", "label": "Sépsis / Choque séptico", "next": "q_mdr", "crumb": "Sépsis/Choque séptico", "issues": ["B6"]},
                {"id": "nenhum", "label": "Nenhum", "next": "r_sem_atb", "crumb": "Sem FR"},
            ],
            "source": src("Figura 1; Tabela 2; 6.1", 3),
            "issues": ["B6"],
        },
        "q_mdr": {
            "type": "question",
            "prompt": "Fatores de risco MDR?",
            "definitionRefs": ["mdr"],
            "options": YES_NO("q_gravidade", "r_ceftriaxone", "FR MDR", "Sem FR MDR"),
            "source": src("Figura 1", 6),
        },
        "q_gravidade": {
            "type": "question",
            "prompt": "Gravidade clínica (sepsis, instabilidade hemodinâmica)?",
            "definitionRefs": ["gravidade"],
            "options": YES_NO("r_meropenem", "r_piptazo", "Gravidade clínica", "Sem gravidade clínica"),
            "source": src("Figura 1", 6, "Caixa 'Piperacilina/Tazobactam … Se gravidade clínica'"),
        },
        "r_sem_atb": {
            "type": "result",
            "antibiotherapy": False,
            "title": "Antibioterapia não recomendada",
            "notes": [
                note("Na diverticulite aguda não complicada não se recomenda a utilização de antibioterapia, exceto em doentes imunodeprimidos ou em sépsis.",
                     src("6.1 Abordagem terapêutica", 3)),
                note("Nem todos os doentes necessitam de internamento, devendo o seguimento em ambulatório ser considerado em indivíduos com diverticulite aguda não complicada, sem comorbilidades relevantes e capazes de tolerar e cumprir terapêutica via oral. Estes devem ser reavaliados dentro de 7 dias para confirmar a resolução do processo inflamatório. A reavaliação antecipada é necessária caso o quadro clínico se deteriore.",
                     src("6.1 Abordagem terapêutica", 4), kind="followup"),
            ],
            "source": [src("Figura 1", 6), src("Tabela 2", 3)],
        },
        "r_ceftriaxone": {
            "type": "result",
            "antibiotherapy": True,
            "title": "Diverticulite — sem FR MDR",
            "firstLine": [regimen("Ceftriaxone 2g id + metronidazol 500mg 8/8h EV",
                                  [drug("Ceftriaxone", "2 g", "EV", "id"), drug("Metronidazol", "500 mg", "EV", "8/8h")],
                                  src("Figura 1", 6))],
            "allergy": [p178_allergy(False)],
            "duration": p178_duration,
            "notes": p178_complicated_interventions + p178_common,
            "source": [src("Figura 1", 6)],
        },
        "r_piptazo": {
            "type": "result",
            "antibiotherapy": True,
            "title": "Diverticulite — FR MDR, sem gravidade clínica",
            "firstLine": [regimen("Piperacilina/Tazobactam 4.5g 6/6h EV",
                                  [drug("Piperacilina/tazobactam", "4,5 g", "EV", "6/6h")], src("Figura 1", 6))],
            "allergy": [p178_allergy(True)],
            "duration": p178_duration,
            "notes": p178_complicated_interventions + p178_common,
            "source": [src("Figura 1", 6)],
        },
        "r_meropenem": {
            "type": "result",
            "antibiotherapy": True,
            "title": "Diverticulite — FR MDR, com gravidade clínica",
            "firstLine": [regimen("Se gravidade clínica (sepsis, instabilidade hemodinâmica): Meropenem 1g 8/8h EV",
                                  [drug("Meropenem", "1 g", "EV", "8/8h")], src("Figura 1", 6))],
            "allergy": [p178_allergy(True)],
            "duration": p178_duration,
            "notes": p178_complicated_interventions + p178_common,
            "source": [src("Figura 1", 6)],
        },
    },
})

# ===========================================================================
# PAC177 / PAC175 — Colecistite aguda / Colangite aguda (same Figure structure)
# ===========================================================================
TOKYO_ORGAN = [
    "Disfunção cardiovascular: hipotensão com necessidade de dopamina ≥5 μg/kg/min ou qualquer dose de noradrenalina",
    "Disfunção neurológica: alteração do estado de consciência",
    "Disfunção respiratória: PaO₂/FiO₂ <300",
    "Disfunção renal: oligúria ou creatinina >2.0 mg/dL",
    "Disfunção hepática: INR >1.5",
    "Disfunção hematológica: plaquetas <100,000/mm³",
]


def biliary_results(prefix, fig_main, fig_allergy, page_main, page_allergy, dur_by_grade, common, metro_text):
    """Build the 4 result nodes shared by PAC175/PAC177 (Figura 'esquemas de tratamento empírico')."""
    metro_addon = regimen(metro_text, [drug("Metronidazol", "500 mg", None, "6/6h")],
                          src(f"{fig_main} — nota 2", page_main), label="Anastomose bilio-entérica",
                          when={"q_anastomose": "sim"})
    metro_addon_allergy = dict(metro_addon, source=src(f"{fig_allergy} — nota 2", page_allergy))

    def cef():
        return regimen("Ceftriaxone² 2g/dia q24h", [drug("Ceftriaxone", "2 g/dia", None, "q24h")], src(fig_main, page_main), issues=["B9"])

    def cip(interval):
        return regimen(f"Ciprofloxacina² 400mg {interval}", [drug("Ciprofloxacina", "400 mg", None, interval)],
                       src(fig_allergy, page_allergy), issues=["B9"])

    return {
        "r_g12_sem": {
            "type": "result", "antibiotherapy": True,
            "title": f"{prefix} Grau I e II — sem fatores de risco para MDR",
            "firstLine": [cef()], "addOns": [metro_addon],
            "allergy": [cip("q12h")], "allergyAddOns": [metro_addon_allergy],
            "duration": dur_by_grade["12"], "notes": common,
            "source": [src(fig_main, page_main), src(fig_allergy, page_allergy)],
        },
        "r_g12_com": {
            "type": "result", "antibiotherapy": True,
            "title": f"{prefix} Grau I e II — com fatores de risco para MDR",
            "firstLine": [regimen("Piperacilina/tazobactam 4,5g q6h", [drug("Piperacilina/tazobactam", "4,5 g", None, "q6h")],
                                  src(fig_main, page_main), issues=["B9", "m8"])],
            "allergy": [cip("q8h")], "allergyAddOns": [metro_addon_allergy],
            "duration": dur_by_grade["12"], "notes": common,
            "source": [src(fig_main, page_main), src(fig_allergy, page_allergy)],
        },
        "r_g3_sem": {
            "type": "result", "antibiotherapy": True,
            "title": f"{prefix} Grau III — sem fatores de risco para MDR",
            "firstLine": [cef()], "addOns": [metro_addon],
            "allergy": [cip("q12h")], "allergyAddOns": [metro_addon_allergy],
            "duration": dur_by_grade["3"], "notes": common,
            "source": [src(fig_main, page_main), src(fig_allergy, page_allergy)],
        },
        "r_g3_com": {
            "type": "result", "antibiotherapy": True,
            "title": f"{prefix} Grau III — com fatores de risco para MDR",
            "firstLine": [regimen("Meropenem 1g q8h", [drug("Meropenem", "1 g", None, "q8h")], src(fig_main, page_main), issues=["B9", "m8"])],
            "allergy": [regimen("A discutir caso a caso", [], src(fig_allergy, page_allergy))],
            "duration": dur_by_grade["3"], "notes": common,
            "source": [src(fig_main, page_main), src(fig_allergy, page_allergy)],
        },
    }


def biliary_questions(grade_options, grade_source, grade_defs):
    return {
        "q_grau": {
            "type": "question", "prompt": "Gravidade ao diagnóstico", "definitionRefs": grade_defs,
            "options": grade_options, "source": grade_source,
        },
        "q_mdr_12": {
            "type": "question", "prompt": "Fatores de risco para MDR?", "definitionRefs": ["mdr"],
            "options": [
                {"id": "sim", "label": "Sim", "next": "q_anastomose_12_com", "crumb": "Com FR MDR"},
                {"id": "nao", "label": "Não", "next": "q_anastomose_12_sem", "crumb": "Sem FR MDR"},
            ],
            "source": grade_source, "answerKey": "q_mdr",
        },
        "q_mdr_3": {
            "type": "question", "prompt": "Fatores de risco para MDR?", "definitionRefs": ["mdr"],
            "options": [
                {"id": "sim", "label": "Sim", "next": "q_anastomose_3_com", "crumb": "Com FR MDR"},
                {"id": "nao", "label": "Não", "next": "q_anastomose_3_sem", "crumb": "Sem FR MDR"},
            ],
            "source": grade_source, "answerKey": "q_mdr",
        },
    }


def anastomosis_nodes(fig_source):
    nodes = {}
    for k, target in [("12_sem", "r_g12_sem"), ("12_com", "r_g12_com"), ("3_sem", "r_g3_sem"), ("3_com", "r_g3_com")]:
        nodes[f"q_anastomose_{k}"] = {
            "type": "question", "prompt": "Anastomose bilio-entérica?",
            "options": [
                {"id": "sim", "label": "Sim", "next": target, "crumb": "Anastomose bilio-entérica"},
                {"id": "nao", "label": "Não", "next": target, "crumb": "Sem anastomose bilio-entérica"},
            ],
            "answerKey": "q_anastomose",
            "source": fig_source,
        }
    return nodes


# ---- PAC177 Colecistite ----------------------------------------------------
p177_common = [
    note("A terapêutica antimicrobiana deve ser iniciada na primeira hora após diagnóstico em situações de sépsis ou choque séptico e idealmente nas primeiras 6 horas nas restantes situações.",
         src("6.2 Abordagem terapêutica", 3), kind="warning"),
    note("A abordagem cirúrgica é a base do tratamento da colecistite aguda e consiste na colecistectomia. Esta intervenção cirúrgica está indicada nas colecistites de todos os graus de gravidade, a não ser que exista contraindicação. A antibioterapia nestas infeções tem um papel adjuvante, existindo pouca evidência para administração de antibioterapia para além das 24 horas pós-cirúrgicas.",
         src("6.2 Abordagem terapêutica", 3), kind="source_control"),
    note("Todos os doentes com infeção da vesicula ou vias biliares devem colher: a) Duas hemoculturas (duas punções diferentes em locais diferentes; de cada punção sangue para frasco de aerobiose e frasco de anaerobiose), sempre antes da toma do antimicrobiano; colher 8-10ml de sangue para cada frasco. b) Todos os doentes submetidos a procedimentos invasivos devem colher líquido biliar para recipiente estéril (o utilizado para urina é adequado) e enviado para cultura; na suspeita de anaeróbios solicitar ao laboratório os recipientes apropriados.",
         src("6.3 Produtos a colher para estudo microbiológico", 4), kind="microbiology"),
    note("Colonização conhecida por agentes multirresistentes: sempre que possível, discutir com a equipa do Programa de Apoio à Prescrição de Antibióticos o melhor esquema de antibioterapia.",
         src("6. Descrição", 2), when={"q_mdr": "sim"}, kind="warning"),
    note("A cobertura de agentes anaeróbios deve ser considerada na presença de anastomose bilioentérica.",
         src("6. Descrição", 2), when={"q_anastomose": "sim"}, kind="warning"),
    note("Se houver isolamento microbiológico em hemoculturas ou no líquido biliar, a antibioterapia deve ser ajustada ao agente isolado e sempre tendo em conta os princípios de utilização de antibióticos de menor espectro e toxicidade.",
         src("Tratamento antimicrobiano dirigido", 5), kind="deescalation"),
    note("Em doentes com controlo do foco eficaz, via oral patente, pelo menos 48h de apirexia e evolução clinica e analítica favorável, a via de tratamento antimicrobiano pode ser alterada para oral. Caso exista bacteremia associada, a transição para antibioterapia oral deve ser discutida caso a caso. Isolamento no líquido biliar ou hemoculturas: tratamento com cobertura para os isolamentos. Culturas negativas sem fatores de risco para MDROs: Cefixima 400mg id. Culturas negativas com fatores de risco para MDROs: discussão individualizada. Anastomose bilioentérica: o esquema deve incluir cobertura de anaeróbios independentemente do agente isolado.",
         src("Tratamento antimicrobiano oral", 5), kind="oral"),
]
p177_bact = note("Em caso de bacteremia — Bacilos gram-negativos: mínimo de 7 dias de tratamento sem necessidade de realização de hemoculturas para documentação da negativação. Outros agentes: a discutir de forma individualizada (pode ser necessário o prolongamento do tratamento, hemoculturas de controlo ou outras intervenções diagnósticas ou terapêuticas).",
                 src("6.5 Duração de antibioterapia e seguimento", 6), kind="duration")
p177_noncx = [
    note("Na ausência de condição cirúrgica para colecistectomia — Doentes submetidos a colecistostomia: 7 dias após drenagem.", src("6.5", 6), kind="duration"),
    note("Na ausência de condição cirúrgica — Doentes a quem não seja possível realizar colecistostomia: a decidir caso a caso, consoante evolução clínica.", src("6.5", 6), kind="duration"),
]
p177_dur = {
    "12": [
        note("Grau I e II: Sem necessidade de antibiótico após a cirurgia.", src("6.5 Duração de antibioterapia e seguimento", 6), kind="duration"),
        note("Em caso de perfuração, alterações enfisematosas ou necrose, constatadas aquando da cirurgia: 4-7 dias após cirurgia.", src("6.5", 6), kind="duration"),
    ] + p177_noncx + [p177_bact],
    "3": [note("Grau III: 4-7 dias após cirurgia.", src("6.5 Duração de antibioterapia e seguimento", 6), kind="duration")] + p177_noncx + [p177_bact],
}
p177_nodes = biliary_questions(
    [
        {"id": "g1", "label": "Grau I (ligeira)", "next": "q_mdr_12", "crumb": "Grau I"},
        {"id": "g2", "label": "Grau II (moderada)", "next": "q_mdr_12", "crumb": "Grau II"},
        {"id": "g3", "label": "Grau III (grave)", "next": "q_mdr_3", "crumb": "Grau III"},
    ],
    src("Tabela 5; Figura 3", 3), ["grau3", "grau2", "grau1"],
)
p177_nodes.update(anastomosis_nodes(src("Figura 3 — nota 2; Figura 4 — nota 2", 4)))
p177_nodes.update(biliary_results(
    "Colecistite aguda", "Figura 3: Esquemas de tratamento empírico na colecistite aguda",
    "Figura 4: Esquemas de tratamento empírico na colecistite aguda em caso de reação de hipersensibilidade",
    4, 5, p177_dur, p177_common, "Associar Metronidazol 500mg 6/6h em caso de anastomose bilio-entérica."))

protocols.append({
    "id": "colecistite",
    "code": "ULSSJ-PAC177-0",
    "title": "Antibioterapia na colecistite aguda",
    "titleEn": "Acute cholecystitis",
    "sourceFile": "docs/protocols/ULSSJ-PAC177-0 Antibioterapia na colecistite aguda.pdf",
    "edition": "Março 2026",
    "approved": "27/03/2026",
    "scope": "Ver documento fonte (secção 2. Âmbito).",
    "keywords": ["colecistite", "vesícula", "Tóquio", "cholecystitis"],
    "definitions": {
        "mdr": {"label": "Fatores de risco para MDROs", "items": MDR_BILIARY, "source": src("6. Descrição; Figura 3 nota 1", 2)},
        "grau3": {"label": "Grau III (grave) — presença de pelo menos um dos critérios", "items": TOKYO_ORGAN, "source": src("Tabela 5", 3)},
        "grau2": {"label": "Grau II (moderada) — presença de pelo menos um dos critérios", "items": [
            "Leucócitos elevados (>18,000/mm³)",
            "Massa palpável e dolorosa no quadrante superior direito do abdómen",
            "Duração das queixas com >72 horas",
            "Inflamação local marcada (colecistite grangrenosa; abcesso pericolecístico; abcesso hepático; peritonite biliar; colecistite enfisematosa)",
        ], "source": src("Tabela 5", 3)},
        "grau1": {"label": "Grau I (ligeira)", "items": ["Não atinge critérios para Grau II ou Grau III ao diagnóstico"], "source": src("Tabela 5", 3)},
        "diagnostico": {"label": "Critérios de diagnóstico de Tóquio (Tabela 4)", "items": [
            "A — Sinais inflamatórios locais: Sinal de Murphy; Massa, dor ou desconforto no quadrante superior direito",
            "B — Inflamação sistémica: Febre; Aumento da proteína C reativa; Leucocitose",
            "C — Imagem: Alterações imagiológicas características de colecistite aguda",
            "Colecistite aguda: pelo menos um critério de A + um critério de B + um critério de C",
            "Suspeita de colecistite aguda: um critério de A e um ou mais critérios de B",
        ], "source": src("6.1 — Tabela 4", 2)},
    },
    "allergyQuestion": {"prompt": "História credível de reação de hipersensibilidade grave aos beta-lactâmicos?", "source": src("Figura 4", 5)},
    "intro": [],
    "start": "q_grau",
    "nodes": p177_nodes,
})

# ---- PAC175 Colangite --------------------------------------------------------
p175_common = [
    note("A terapêutica antimicrobiana deve ser iniciada na primeira hora após diagnóstico em situações de sépsis ou choque séptico e idealmente nas primeiras 6 horas nas restantes situações.",
         src("6.2 Abordagem terapêutica", 3), kind="warning"),
    note("A drenagem da via biliar é a base do tratamento da colangite aguda. O papel da antibioterapia nestas infeções é adjuvante, permitindo sobretudo que a descompressão das vias biliares seja realizada de forma não emergente.",
         src("6.2 Abordagem terapêutica", 3), kind="source_control"),
    note("Grau I (Ligeira): Antibioterapia e cuidados de suporte gerais. Considerar drenagem biliar se ausência de resposta ao tratamento inicial.",
         src("Tabela 3", 4), when={"q_grau": "g1"}, kind="source_control"),
    note("Grau II (Moderada): Antibioterapia e cuidados de suporte gerais. Está indicada a drenagem biliar precoce, endoscópica ou percutânea.",
         src("Tabela 3", 4), when={"q_grau": "g2"}, kind="source_control"),
    note("Grau III (Grave): Antibioterapia inicial e cuidados de suporte otimizados. Drenagem biliar urgente.",
         src("Tabela 3", 4), when={"q_grau": "g3"}, kind="source_control"),
] + [dict(n, source=src(n["source"]["section"], {"Tratamento antimicrobiano dirigido": 6}.get(n["source"]["section"], n["source"]["page"]))) for n in p177_common[2:6]] + [
    note("Em doentes com controlo do foco eficaz, via oral patente, pelo menos 48h de apirexia e evolução clinica e analítica favorável, a via de tratamento antimicrobiano pode ser alterada para oral. Caso exista bacteremia associada, a transição para antibioterapia oral deve ser discutida caso a caso. Isolamento no líquido biliar ou hemoculturas: tratamento com cobertura para os isolamentos. Culturas negativas sem fatores de risco para MDROs: Cefixima 400mg id. Culturas negativas com fatores de risco para MDROs: discussão individualizada. Anastomose bilioentérica: o esquema deve incluir cobertura de anaeróbios independentemente do agente isolado (metronidazol 500mg 6/6h).",
         src("Tratamento antimicrobiano oral", 6), kind="oral"),
    note("Em doentes com prótese na via biliar, recomenda-se idealmente substituição ou remoção da mesma. Na sua impossibilidade, a duração da antibioterapia deve ser decidida caso a caso.",
         src("6.5 Duração de antibioterapia e seguimento", 7), kind="source_control"),
]
p175_bact = dict(p177_bact, source=src("6.5 Duração de antibioterapia e seguimento", 7))
p175_late = note("Em doentes em que a descompressão da via biliar só seja possível tardiamente e para quem já tenham sido cumpridos 7 dias de antibioterapia com boa evolução, pode ser equacionada a suspensão de antibioterapia nas 24h após o procedimento.",
                 src("6.5", 7), kind="duration")
p175_dur = {
    "12": [
        note("Se colangite Grau I com boa evolução clinica e analítica, em que não se considere necessária descompressão da via biliar, o tratamento será de 7 dias.",
             src("6.5 Duração de antibioterapia e seguimento", 6), when={"q_grau": "g1"}, kind="duration"),
        note("Se colangite Grau I com má evolução ou Grau II ou III, o tratamento antibiótico deve ser mantido 4 a 7 dias após a descompressão.",
             src("6.5 Duração de antibioterapia e seguimento", 6), kind="duration"),
        p175_late, p175_bact,
    ],
    "3": [
        note("Se colangite Grau I com má evolução ou Grau II ou III, o tratamento antibiótico deve ser mantido 4 a 7 dias após a descompressão.",
             src("6.5 Duração de antibioterapia e seguimento", 6), kind="duration"),
        p175_late, p175_bact,
    ],
}
p175_nodes = biliary_questions(
    [
        {"id": "g1", "label": "Grau I (ligeira)", "next": "q_mdr_12", "crumb": "Grau I"},
        {"id": "g2", "label": "Grau II (moderada)", "next": "q_mdr_12", "crumb": "Grau II"},
        {"id": "g3", "label": "Grau III (grave)", "next": "q_mdr_3", "crumb": "Grau III"},
    ],
    src("Tabela 2; Figura 1", 3), ["grau3", "grau2", "grau1"],
)
p175_nodes.update(anastomosis_nodes(src("Figura 1 — nota 2; Figura 2 — nota 2", 5)))
p175_nodes.update(biliary_results(
    "Colangite aguda", "Figura 1: Esquemas de tratamento empírico na colangite aguda",
    "Figura 2: Esquemas de tratamento empírico na colangite aguda em caso de reação de hipersensibilidade aos beta-lactâmicos",
    5, 5, p175_dur, p175_common, "Associar Metronidazol 500mg 6/6h em caso de anastomose bilio-entérica."))
protocols.append({
    "id": "colangite",
    "code": "ULSSJ-PAC175-0",
    "title": "Antibioterapia nas infeções das vias biliares",
    "titleEn": "Biliary tract infections (acute cholangitis)",
    "sourceFile": "docs/protocols/ULSSJ-PAC175-0 Antibioterapia nas infecoes das vias biliares.pdf",
    "edition": "Março 2026",
    "approved": "27/03/2026",
    "scope": "É aplicável aos doentes adultos com patologia infeciosa relacionada com as vias biliares.",
    "keywords": ["colangite", "vias biliares", "Tóquio", "cholangitis", "CPRE"],
    "definitions": {
        "mdr": {"label": "Fatores de risco para MDROs", "items": MDR_BILIARY, "source": src("6. Descrição; Figura 1 nota 1", 2)},
        "grau3": {"label": "Grau III — presença de pelo menos 1 dos seguintes achados", "items": TOKYO_ORGAN, "source": src("Tabela 2", 3)},
        "grau2": {"label": "Grau II — pelo menos 2 dos seguintes achados", "items": [
            "Leucócitos alterados (>12,000/mm³ or <4,000/mm³)",
            "Febre elevada (≥39°C)",
            "Idade ≥75 anos",
            "Hiperbilirrubinemia (total ≥5 mg/dL)",
            "Hipoalbuminemia (<0.7 x limite superior normal)",
        ], "source": src("Tabela 2", 3)},
        "grau1": {"label": "Grau I", "items": ["Não atinge critérios para Grau II ou Grau III ao diagnóstico"], "source": src("Tabela 2", 3)},
        "diagnostico": {"label": "Critérios de diagnóstico de Tóquio de Colangite Aguda (Tabela 1)", "items": [
            "A — Inflamação sistémica: Febre (>38°C) e/ou arrepios; Leucócitos <4 ou >10 x1,000/μL e/ou Prot C Reactiva ≥ 10 mg/L",
            "B — Colestase: Icterícia (bilirrubina total ≥2 mg/dL); Níveis de FA, GGT, AST, ALT >1.5x LSN",
            "C — Imagem: Dilatação da árvore biliar; Evidência da etiologia na imagiologia: estenose, litíase, prótese, etc.",
            "Colangite: pelo menos um critério de A + um critério de B + um critério de C",
            "Suspeita de colangite: um critério de A e um ou mais critérios de B ou C",
        ], "source": src("6.1 — Tabela 1", 2)},
    },
    "allergyQuestion": {"prompt": "História credível de reação de hipersensibilidade grave aos beta-lactâmicos (angioedema, dificuldade respiratória e urticária)?",
                        "source": src("6.4", 5)},
    "intro": [],
    "start": "q_grau",
    "nodes": p175_nodes,
})

# ===========================================================================
# PAC174 — Infeção associada a pancreatite aguda
# ===========================================================================
p174_allergy = lambda mdr: regimen(  # noqa: E731
    "Alergia a beta-lactâmicos: Ciprofloxacina 400mg 12/12h (se FR MDR: 8/8h) EV + Metronidazol 500mg 8/8h EV",
    [drug("Ciprofloxacina", "400 mg", "EV", "8/8h" if mdr else "12/12h"), drug("Metronidazol", "500 mg", "EV", "8/8h")],
    src("Fluxograma (p. 3); 6.2.3", 3),
)
p174_common = [
    note("As doses de antibioterapia devem ser ajustadas à função renal.", src("6.2.3", 5), kind="renal"),
    note("Hemoculturas (se o doente tiver febre): duas amostras (duas punções em locais diferentes; de cada punção 20mL: 10 mL para frasco de aerobiose e 10 mL para frasco de anaerobiose); se possível antes da primeira toma do antimicrobiano. Líquido de drenagem (em doentes em que seja considerada drenagem percutânea ou transgástrica): aerobiose em frasco estéril; anaerobiose em recipiente apropriado a solicitar ao laboratório.",
         src("1. Produtos a colher para estudo microbiológico", 4), kind="microbiology"),
    note("A punção aspirativa não está indicada por rotina e não deve ser um critério para iniciar ou não antibioterapia (uma punção aspirativa negativa não exclui indicação para antibiótico).",
         src("6.1", 4)),
    note("O tratamento antifúngico não deve ser utilizado por rotina na necrose pancreática infetada. Pode ser considerada a associação de antifúngico em doentes com disfunção grave de órgão ou instabilidade hemodinâmica atribuíveis à infeção, a suspender após estabilidade clínica e caso não exista evidência de infeção fúngica.",
         src("6.2.3", 5), kind="warning", issues=["m12"]),
    note("Se houver isolamento microbiológico em hemoculturas ou no líquido de drenagem aquando da cirurgia, a antibioterapia deve ser ajustada ao agente isolado e sempre tendo em conta os princípios de utilização dos antibióticos com menor espectro e toxicidade.",
         src("6.2.3", 5), kind="deescalation"),
    note("É possível a passagem a terapia oral após melhoria clínica, analítica e imagiológica sob terapia endovenosa, via oral patente e uma alternativa antibiótica oral satisfatória em termos farmacocinéticos e com probabilidade de reter atividade contra os agentes presumidos ou identificados. O metronidazol EV deve assim que possível passar para via oral. Em situação em que não exista isolamento de agente, e na ausência de gravidade ou fatores de risco para agentes multirresistentes, pode ser considerada caso a caso a transição para antibioterapia oral com Cefixima 400mg id + Metronidazol 500mg q8h.",
         src("6.3 Duração de antibioterapia e seguimento", 6), kind="oral"),
    note("Em pacientes clinicamente estáveis sob antibioterapia, adiar a necrosectomia até 30 dias após a admissão hospitalar inicial está associado a uma mortalidade reduzida. Se não houver resposta à antibioterapia num curto espaço de tempo ou se a situação clínica piorar, a necrosectomia/desbridamento deve ser realizada. Após os 30 dias, no caso de uma coleção necrótica com uma parede bem definida e material liquefeito no interior, a drenagem pode ser considerada, seja por via endoscópica (preferencial) ou radiológica. Caso nenhum destes métodos seja possível ou eficaz, deve ser considerada uma abordagem cirúrgica.",
         src("6.4 Abordagem cirúrgica", 6), kind="source_control"),
]
p174_dur = [note("A duração da antibioterapia na pancreatite deve ser individualizada. A suspensão de antibioterapia pode ser ponderada após melhoria clínica e imagiológica sustentadas. A extensão da infeção e a existência de uma abordagem para controlo do foco devem ser tidos em conta na decisão da duração do tratamento.",
                 src("6.3 Duração de antibioterapia e seguimento", 6), kind="duration")]
protocols.append({
    "id": "pancreatite",
    "code": "ULSSJ-PAC174-0",
    "title": "Antibioterapia na infeção associada à pancreatite aguda",
    "titleEn": "Infection associated with acute pancreatitis",
    "sourceFile": "docs/protocols/ULSSJ-PAC174-0 Antibioterapia na infecao associada a pancreatite aguda.pdf",
    "edition": "Março 2026",
    "approved": "27/03/2026",
    "scope": "É aplicável aos doentes adultos com patologia infeciosa relacionada com pancreatite aguda.",
    "keywords": ["pancreatite", "necrose", "WON", "pancreatitis"],
    "pending": True,
    "issues": ["B1"],
    "definitions": {
        "mdr": {"label": "Fatores de risco para infeções por agentes multirresistentes", "items": MDR_STD, "source": src("Fluxograma nota 2; 6.2", 3)},
        "necrose_infetada": {"label": "Necrose (peripancreática) infetada", "items": [
            "Deterioração clínica 7-10 dias após início do quadro, com sinais sistémicos de infeção e imagiologia abdominal que demonstre a presença de gás no interior da loca necrose",
            "Se gravidade clínica significativa, considerar início de antibioterapia mesmo na ausência de gás no interior da loca de necrose",
            "Se dúvida sobre indicação para antibioterapia: em doentes clinicamente estáveis, procalcitonina < 1 ng/mL deve levar a suspender ou não iniciar antibiótico",
        ], "source": src("Fluxograma nota 1", 3)},
        "gravidade": {"label": "Gravidade clínica", "items": ["Sepsis", "Instabilidade hemodinâmica"], "source": src("Fluxograma", 3)},
    },
    "allergyQuestion": {"prompt": "Alergia a beta-lactâmicos?", "source": src("Fluxograma", 3)},
    "intro": [],
    "start": "q_suspeita",
    "nodes": {
        "q_suspeita": {
            "type": "question",
            "prompt": "Suspeita de necrose (peri)pancreática infetada?",
            "help": "Na ausência de outros achados sugestivos de infeção, não está recomendado o início de antibioterapia baseada na procalcitonina isoladamente.",
            "definitionRefs": ["necrose_infetada"],
            "options": YES_NO("q_mdr", "r_sem_atb", "Suspeita de necrose infetada", "Sem suspeita de necrose infetada"),
            "source": src("Fluxograma", 3),
        },
        "q_mdr": {
            "type": "question",
            "prompt": "Fatores de risco para agentes multirresistentes MDR?",
            "definitionRefs": ["mdr"],
            "options": YES_NO("q_gravidade", "r_ceftriaxone", "FR MDR", "Sem FR MDR"),
            "source": src("Fluxograma", 3),
            "issues": ["B1", "m10"],
        },
        "q_gravidade": {
            "type": "question",
            "prompt": "Gravidade clínica (sepsis, instabilidade hemodinâmica)?",
            "definitionRefs": ["gravidade"],
            "options": YES_NO("r_meropenem", "r_piptazo", "Gravidade clínica", "Sem gravidade clínica"),
            "source": src("Fluxograma", 3),
            "issues": ["B1"],
        },
        "r_sem_atb": {
            "type": "result", "antibiotherapy": False,
            "title": "Sem indicação para antibioterapia",
            "notes": p174_common[2:3],
            "source": [src("Fluxograma", 3)],
        },
        "r_ceftriaxone": {
            "type": "result", "antibiotherapy": True, "pending": True,
            "title": "Pancreatite — necrose infetada (ramo 'sem FR MDR' do fluxograma)",
            "firstLine": [regimen("Ceftriaxone 2g id + metronidazol 500mg 8/8h EV",
                                  [drug("Ceftriaxone", "2 g", "EV", "id"), drug("Metronidazol", "500 mg", "EV", "8/8h")],
                                  src("Fluxograma; 6.2.1", 3))],
            "allergy": [p174_allergy(False)],
            "duration": p174_dur, "notes": p174_common,
            "source": [src("Fluxograma", 3), src("6.2.1", 5)], "issues": ["B1"],
        },
        "r_piptazo": {
            "type": "result", "antibiotherapy": True, "pending": True,
            "title": "Pancreatite — necrose infetada (ramo 'FR MDR, sem gravidade' do fluxograma)",
            "firstLine": [regimen("Piperacilina/Tazobactam 4.5g 6/6h EV",
                                  [drug("Piperacilina/tazobactam", "4,5 g", "EV", "6/6h")], src("Fluxograma; 6.2.2", 3))],
            "allergy": [p174_allergy(True)],
            "duration": p174_dur, "notes": p174_common,
            "source": [src("Fluxograma", 3), src("6.2.2", 5)], "issues": ["B1"],
        },
        "r_meropenem": {
            "type": "result", "antibiotherapy": True, "pending": True,
            "title": "Pancreatite — necrose infetada (ramo 'FR MDR, com gravidade' do fluxograma)",
            "firstLine": [regimen("Se gravidade clínica (sepsis, instabilidade hemodinâmica): Meropenem 1g 8/8h EV",
                                  [drug("Meropenem", "1 g", "EV", "8/8h")], src("Fluxograma; 6.2.2", 3))],
            "allergy": [p174_allergy(True)],
            "duration": p174_dur, "notes": p174_common,
            "source": [src("Fluxograma", 3), src("6.2.2", 5)], "issues": ["B1"],
        },
    },
})

# ===========================================================================
# PAC179 — Úlcera gastroduodenal perfurada
# ===========================================================================
P179_ENTERO = regimen(
    "*Considerar adicionar cobertura para Enterococcus spp (vancomicina 15-20mg/kg/8-12h, ou, em alternativa, daptomicina 8-10 mg/kg/dia ou linezolide 600mg/12h) em: doentes com valvulopatia, prótese valvular ou história de endocardite, imunossupressão, infeção nosocomial ou tratamento prévio com cefalosporinas ou quinolonas.",
    [drug("Vancomicina", "15-20 mg/kg", None, "8-12h"), drug("Daptomicina", "8-10 mg/kg/dia", None, "id", "alternativa"),
     drug("Linezolide", "600 mg", None, "12/12h", "alternativa")],
    src("6.3 (nota *); Figura 1", 4), label="± cobertura de Enterococcus spp*", issues=["m9"],
)
P179_CANDIDA = regimen(
    "**Considerar adicionar cobertura para Candida spp nos seguintes casos: doente crítico, doente sob alimentação parentérica, uso de terapêutica de substituição renal contínua, colonização multifocal por Candida spp, deiscência de sutura gástrica ou duodenal. O antífúngico de eleição é a caspofungina 70mg dose carga + 50mg/24h.",
    [drug("Caspofungina", "70 mg (dose de carga) + 50 mg", None, "24/24h")],
    src("6.3 (nota **); Figura 1", 4), label="± cobertura de Candida spp**",
)
p179_allergy_simple = regimen(
    "Se alergia com indicação para evicção de β-lactâmicos: ciprofloxacina 400mg /8h + metronidazol 500 mg /8h",
    [drug("Ciprofloxacina", "400 mg", None, "8/8h"), drug("Metronidazol", "500 mg", None, "8/8h")],
    src("Figura 1", 6), issues=["B9"],
)
p179_allergy_tige = regimen(
    "Se alergia com indicação para evicção de β-lactâmicos: ciprofloxacina 400mg/8h + tigeciclina (100 mg e depois 50 mg /12h)",
    [drug("Ciprofloxacina", "400 mg", None, "8/8h"), drug("Tigeciclina", "100 mg (dose inicial) e depois 50 mg", None, "12/12h")],
    src("Figura 1; 6.3", 6), issues=["B2", "B9"],
)
p179_common = [
    note("Recomenda-se antibioterapia empírica em todos os doentes com úlceras pépticas perfuradas. A perfuração de úlcera péptica deve ser tratada como uma peritonite secundária adquirida na comunidade.",
         src("6.1 Abordagem terapêutica", 2)),
    note("Abordagem cirúrgica: Sutura laparoscópica ou via aberta, simples ou double layer com ou sem patch omental (procedimento padrão). Gastrectomia distal (grandes perfurações próximas ao piloro; suspeita de malignidade). Biópsia indicada em todas as úlceras gástricas.",
         src("Figura 1", 6), kind="source_control"),
    note("Hemoculturas a todos os doentes com critérios de sépsis (40-60 mL de sangue, a distribuir por 4-6 frascos, punções em locais diferentes, 20 mL por punção: 10 mL aerobiose + 10 mL anaerobiose), antes do início de antibioterapia. Líquido intraperitoneal colhido intraoperatoriamente para recipiente estéril (solicitar recipientes para anaeróbios) em todos os doentes submetidos a cirurgia ou drenagem. Produtos colhidos por zaragatoa, aspiração superficial de pús ou através de drenos colocados há mais de 24 horas não estão recomendados.",
         src("6.2 Produtos a colher para estudo microbiológico", 3), kind="microbiology"),
    note("O esquema antibiótico deve ser de-escalado assim que possível tendo em conta os agentes isolados nos produtos microbiológicos invasivos colhidos.",
         src("6.4", 5), kind="deescalation"),
    note("A antibioterapia pode ser completada por via oral caso exista evolução clínica favorável, controlo adequado do foco e um isolamento microbiológico suscetível a antibióticos eficazes por via oral. Em doentes sem critérios de sépsis e sem fatores de mau prognóstico, mas sem isolamento microbiológico pode ser considerado completar o tratamento por via oral com cefixime 400 mg/dia + metronidazol 500 mg 8/8h.",
         src("6.4", 5), kind="oral"),
]
p179_dur = [
    note("Se a evolução clínica for favorável (apirexia, tolerância à alimentação oral, normalização da contagem de leucócitos e descida significativa de parâmetros inflamatórios), a antibioterapia deve ser interrompida após 3-5 dias. Caso o curso seja desfavorável ou surjam complicações locais, a duração de antibioterapia deve ser decidida de acordo com a evolução clínica e imagiológica.",
         src("6.4 Duração de antibioterapia e seguimento", 5), kind="duration"),
]
p179_dur_af = p179_dur + [
    note("A terapêutica antifúngica (caspofungina 50mg/24h), quando iniciada, deve ser administrada durante 7-10 dias ou até exame micológico de líquido peritoneal negativo. Nos casos em que exista candidemia, o antifúngico deve ser prolongado pelo menos até 14 dias após hemoculturas de controlo negativas.",
         src("6.4", 5), kind="duration"),
]
protocols.append({
    "id": "ulcera-perfurada",
    "code": "ULSSJ-PAC179-0",
    "title": "Antibioterapia na úlcera gastroduodenal perfurada",
    "titleEn": "Perforated gastroduodenal ulcer",
    "sourceFile": "docs/protocols/ULSSJ-PAC179-0 Antibioterapia na ulcera gastroduodenal perfurada.pdf",
    "edition": "Março 2026",
    "approved": "27/03/2026",
    "scope": "Ver documento fonte (secção 2. Âmbito).",
    "keywords": ["úlcera", "perfurada", "péptica", "gastroduodenal", "peritonite", "perforated ulcer"],
    "pending": True,
    "issues": ["B2"],
    "definitions": {
        "mdr": {"label": "Fatores de risco para infeções por MDROs", "items": MDR_STD, "source": src("6.3; Figura 1", 3)},
        "mau_prognostico": {"label": "Fatores de mau prognóstico", "items": [
            "Idade > 70 anos",
            "Desnutrição (hipoalbuminemia)",
            "Imunossupressão (doente sob corticoterapia em alta dose (>20 mg/dia) ou outros imunossupressores, imunodeficiência primária, sida, neoplasia sob quimioterapia, diabetes mellitus com mau controlo metabólico)",
            "Comorbilidades significativas: diabetes mellitus com mau controlo metabólico, cirrose hepática, DRC em hemodiálises, neoplasia ativa, DPOC avançada",
        ], "source": src("6.3", 4), "issues": ["m9"]},
        "sepsis": {"label": "Sépsis", "items": ["Infeção associada a disfunção orgânica potencialmente ameaçadora de vida (Surviving Sepsis Campaign 2023)"],
                   "source": src("6.2 nota 1", 3)},
    },
    "allergyQuestion": {"prompt": "Alergia com indicação para evicção de β-lactâmicos?", "source": src("Figura 1", 6)},
    "intro": [],
    "start": "q_mdr",
    "nodes": {
        "q_mdr": {
            "type": "question",
            "prompt": "Fatores de risco para MDROs?",
            "definitionRefs": ["mdr"],
            "options": YES_NO("q_gravidade", "r_ceftriaxone", "FR MDROs", "Sem FR MDROs"),
            "source": src("Figura 1", 6),
            "issues": ["B2"],
        },
        "q_gravidade": {
            "type": "question",
            "prompt": "Gravidade ou fatores de mau prognóstico?",
            "definitionRefs": ["sepsis", "mau_prognostico"],
            "options": YES_NO("r_meropenem", "r_piptazo", "Gravidade / mau prognóstico", "Sem gravidade nem mau prognóstico"),
            "source": src("Figura 1", 6),
            "issues": ["B2"],
        },
        "r_ceftriaxone": {
            "type": "result", "antibiotherapy": True, "pending": True,
            "title": "Úlcera perfurada — sem FR MDROs (ramo do fluxograma)",
            "firstLine": [regimen("Ceftriaxone 2g /24h + metronidazol 500 mg /8h",
                                  [drug("Ceftriaxone", "2 g", None, "24/24h"), drug("Metronidazol", "500 mg", None, "8/8h")],
                                  src("Figura 1; 6.3", 6), issues=["B9"])],
            "allergy": [p179_allergy_simple],
            "duration": p179_dur, "notes": p179_common,
            "source": [src("Figura 1", 6), src("6.3", 4)], "issues": ["B2"],
        },
        "r_piptazo": {
            "type": "result", "antibiotherapy": True, "pending": True,
            "title": "Úlcera perfurada — FR MDROs, sem gravidade nem fatores de mau prognóstico (ramo do fluxograma)",
            "firstLine": [regimen("Piperacilina-tazobactam 4,5g /6h", [drug("Piperacilina/tazobactam", "4,5 g", None, "6/6h")],
                                  src("Figura 1; 6.3", 6), issues=["B9"])],
            "addOns": [P179_ENTERO, P179_CANDIDA],
            "allergy": [p179_allergy_tige],
            "duration": p179_dur_af, "notes": p179_common,
            "source": [src("Figura 1", 6), src("6.3", 4)], "issues": ["B2"],
        },
        "r_meropenem": {
            "type": "result", "antibiotherapy": True, "pending": True,
            "title": "Úlcera perfurada — FR MDROs, com gravidade ou fatores de mau prognóstico",
            "firstLine": [regimen("Meropenem 1g/8h", [drug("Meropenem", "1 g", None, "8/8h")], src("Figura 1; 6.3", 6), issues=["B9"])],
            "addOns": [P179_ENTERO, P179_CANDIDA],
            "allergy": [p179_allergy_tige],
            "duration": p179_dur_af, "notes": p179_common,
            "source": [src("Figura 1", 6), src("6.3", 4)], "issues": ["B2"],
        },
    },
})

# ===========================================================================
# PAC173 — Abcesso anorretal
# ===========================================================================
p173_allergy_mdr = regimen(
    "Se alergia com indicação para evicção de a ß-lactâmicos: Ciprofloxacina 400mg EV q8h + Metronidazol 500mg IV 8/8H",
    [drug("Ciprofloxacina", "400 mg", "EV", "q8h"), drug("Metronidazol", "500 mg", "IV", "8/8h")],
    src("Tabela 2", 5),
)
p173_common = [
    note("Nota: as doses de antibioterapia apresentadas são as recomendadas para doentes com função renal normal, devendo ser ajustadas se necessário.",
         src("6.3", 4), kind="renal"),
    note("A intervenção cirúrgica com incisão e drenagem é a base do tratamento do AA, com ou sem fístula associada, e deve ser realizada em todos os doentes, independentemente das comorbilidades ou gravidade clínica.",
         src("6.1 Abordagem terapêutica", 2), kind="source_control"),
    note("Recomenda-se a colheita do pús da drenagem dos abcessos anorretais, com envio para microbiologia, apenas nos doentes em que está previsto início de antibioterapia. Na presença de critérios de gravidade clínica e repercussão sistémica, devem ser colhidos dois sets de hemoculturas (duas punções em locais diferentes, 20 ml de sangue em cada punção, divididos em frascos de aerobiose e anaerobiose), preferencialmente antes do início da antibioterapia.",
         src("6.2 Produtos a colher para estudo microbiológico", 3), kind="microbiology"),
    note("Na presença de um isolamento de agente, deve ser feito o respetivo ajuste de antibioterapia de modo a escolher o fármaco com o espectro mais curto possível.",
         src("6.4 Tratamento antimicrobiano dirigido", 6), kind="deescalation"),
    note("Perante uma drenagem bem-sucedida e evolução clínica favorável, a transição para antibioterapia oral deve ocorrer o mais precocemente possível, idealmente ajustada ao isolamento. Em doentes sem critérios de sépsis e sem fatores de mau prognóstico e sem isolamento microbiológico pode ser considerado completar o tratamento via oral com cefixime 400mg/dia + metronidazol 500mg 8/8h.",
         src("6.5 Transição antibioterapia oral", 6), kind="oral", issues=["m13"]),
]
p173_dur = [note("A duração de antibioterapia (quando recomendada) é de 5 dias após a drenagem, mas deve ser individualizada tendo em conta a extensão da infeção e a resposta ao tratamento.",
                 src("6.6 Duração da antibioterapia", 6), kind="duration")]
protocols.append({
    "id": "abcesso-anorretal",
    "code": "ULSSJ-PAC173-0",
    "title": "Abordagem terapêutica do abcesso anorretal",
    "titleEn": "Anorectal abscess",
    "sourceFile": "docs/protocols/ULSSJ-PAC173-0 Abordagem terapeutica do abcesso anorretal.pdf",
    "edition": "Março 2026",
    "approved": "27/03/2026",
    "scope": "Ver documento fonte (secção 2. Âmbito).",
    "keywords": ["abcesso", "anorretal", "perianal", "fístula", "anorectal abscess"],
    "definitions": {
        "mdr": {"label": "Fatores de risco major para infeções por MDROs", "items": MDR_STD, "source": src("6.3", 4)},
        "fr_clinico": {"label": "Fatores de risco clínico", "items": [
            "Celulite perianal/perineal extensa;",
            "Abcesso recidivado;",
            "Associado a DII;",
            "Diabetes Mellitus com mau controlo metabólico;",
            "Cirrose hepática;",
            "Doença renal crónica;",
            "Portadores de próteses valvulares cardíacas;",
            "Utilização de corticoterapia sistémica ou outra terapêutica imunomoduladora em ambulatório;",
            "Outras formas de imunossupressão - imunodeficiência primária, SIDA, neoplasia sob quimioterapia.",
        ], "source": src("6.3; Tabela 1; Tabela 2", 4), "issues": ["B7"]},
        "gravidade": {"label": "Gravidade clínica", "items": [
            "Infeção associada a disfunção orgânica potencialmente ameaçadora de vida (6.1)",
            "Sepsis, instabilidade hemodinâmica (Figura 1)",
        ], "source": src("6.1; Figura 1", 2)},
    },
    "allergyQuestion": {"prompt": "Alergia com indicação para evicção de β-lactâmicos?", "source": src("Tabela 2", 5)},
    "intro": [],
    "start": "q_fistula",
    "nodes": {
        "q_fistula": {
            "type": "question",
            "prompt": "Evidência de fístula?",
            "help": "Perante a presença de fístula anorretal, a decisão de realizar fistulotomia concomitante versus tardia deve ser tomada após pesar os benefícios (cicatrização) versus os riscos (incontinência) para cada paciente, sendo geralmente mais favorável realizar o procedimento quando o edema e a inflamação diminuem.",
            "options": [
                {"id": "sim", "label": "Sim — Drenagem de abcesso +/- fistulotomia", "next": "q_criterios", "crumb": "Fístula: drenagem +/- fistulotomia"},
                {"id": "nao", "label": "Não — Drenagem de abcesso", "next": "q_criterios", "crumb": "Sem fístula: drenagem"},
            ],
            "source": src("Figura 1", 7),
        },
        "q_criterios": {
            "type": "question",
            "prompt": "Critérios para antibioterapia?",
            "definitionRefs": ["gravidade", "fr_clinico"],
            "options": [
                {"id": "gravidade", "label": "Gravidade clínica", "next": "q_mdr_grave", "crumb": "Gravidade clínica"},
                {"id": "fr_clinico", "label": "Fatores de risco clínico (sem gravidade clínica)", "next": "q_mdr_fr", "crumb": "FR clínico"},
                {"id": "nao", "label": "Não", "next": "r_vigilancia", "crumb": "Sem critérios"},
            ],
            "source": src("Figura 1; Tabela 1; 6.1", 3),
            "issues": ["B7"],
        },
        "q_mdr_grave": {
            "type": "question", "prompt": "Fatores de risco MDR?", "definitionRefs": ["mdr"],
            "options": YES_NO("r_meropenem", "r_ceftriaxone", "FR MDR", "Sem FR MDR"),
            "source": src("Figura 1; Tabela 2", 7), "answerKey": "q_mdr", "issues": ["m10"],
        },
        "q_mdr_fr": {
            "type": "question", "prompt": "Fatores de risco MDR?", "definitionRefs": ["mdr"],
            "options": YES_NO("r_piptazo", "r_ceftriaxone", "FR MDR", "Sem FR MDR"),
            "source": src("Figura 1; Tabela 2", 7), "answerKey": "q_mdr", "issues": ["m10"],
        },
        "r_vigilancia": {
            "type": "result", "antibiotherapy": False,
            "title": "Vigilância sem antibiótico",
            "notes": [note("A antibioterapia após drenagem de abcesso anorretal não complicado não está recomendada por rotina pois não diminui o tempo de recuperação e não reduz recorrências ou surgimento de fístula.",
                           src("6.1", 2))] + p173_common[1:2],
            "source": [src("Figura 1", 7), src("Tabela 2", 5)],
        },
        "r_ceftriaxone": {
            "type": "result", "antibiotherapy": True,
            "title": "Abcesso anorretal — sem FR MDR (independentemente da gravidade)",
            "firstLine": [
                regimen("Opção EV: Ceftriaxone 2g IV id + Metronidazol 500mg IV q8h",
                        [drug("Ceftriaxone", "2 g", "IV", "id"), drug("Metronidazol", "500 mg", "IV", "q8h")], src("Tabela 2; Figura 1", 5), label="Opção EV"),
                regimen("Opção oral: Cefixima 400mg PO id + Metronidazol 500mg PO 8/8H",
                        [drug("Cefixima", "400 mg", "PO", "id"), drug("Metronidazol", "500 mg", "PO", "8/8h")], src("Tabela 2", 5), label="Opção oral", issues=["B7"]),
            ],
            "allergy": [
                regimen("Opção EV: Ciprofloxacina 400mg IV 12/12H + Metronidazol 500mg IV 8/8H",
                        [drug("Ciprofloxacina", "400 mg", "IV", "12/12h"), drug("Metronidazol", "500 mg", "IV", "8/8h")], src("Tabela 2; Figura 1", 5), label="Opção EV"),
                regimen("Opção oral: Ciprofloxacina 500mg PO 12/12H + Metronidazol 500mg PO 8/8H",
                        [drug("Ciprofloxacina", "500 mg", "PO", "12/12h"), drug("Metronidazol", "500 mg", "PO", "8/8h")], src("Tabela 2", 5), label="Opção oral", issues=["B7"]),
            ],
            "duration": p173_dur, "notes": p173_common,
            "source": [src("Tabela 2", 5), src("Figura 1", 7)],
        },
        "r_piptazo": {
            "type": "result", "antibiotherapy": True,
            "title": "Abcesso anorretal — FR MDR, sem gravidade clínica",
            "firstLine": [regimen("Piperacilina/tazobactam 4.5g /6h IV", [drug("Piperacilina/tazobactam", "4,5 g", "IV", "6/6h")], src("Tabela 2; Figura 1", 5))],
            "allergy": [p173_allergy_mdr],
            "duration": p173_dur, "notes": p173_common,
            "source": [src("Tabela 2", 5), src("Figura 1", 7)],
        },
        "r_meropenem": {
            "type": "result", "antibiotherapy": True,
            "title": "Abcesso anorretal — FR MDR, com gravidade clínica",
            "firstLine": [regimen("Meropenem 1g/8h IV", [drug("Meropenem", "1 g", "IV", "8/8h")], src("Tabela 2; Figura 1", 5))],
            "allergy": [p173_allergy_mdr],
            "duration": p173_dur, "notes": p173_common,
            "source": [src("Tabela 2", 5), src("Figura 1", 7)],
        },
    },
})

# Display order (home grid)
ORDER = ["apendicite", "diverticulite", "colecistite", "colangite", "pancreatite", "ulcera-perfurada", "abcesso-anorretal"]
protocols.sort(key=lambda p: ORDER.index(p["id"]))

doc = {
    "schemaVersion": 1,
    "generatedBy": "tools/build_protocols.py",
    "institution": "Unidade Local de Saúde São João (ULS São João)",
    "status": "DRAFT — pending clinical confirmation of open issues in CLINICAL_AUDIT.md",
    "disclaimer": "Ferramenta de apoio à decisão baseada nos Protocolos de Atuação Clínica da ULS São João. Não substitui o juízo clínico.",
    "protocols": protocols,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {OUT.relative_to(ROOT)} ({len(protocols)} protocols)")
