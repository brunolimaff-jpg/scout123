"""
utils/pdf_export.py — RAPTOR Intelligence Report PDF Export
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import tempfile
from scout_types import DossieCompleto

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False
    FPDF = object


class RaptorPDF(FPDF if HAS_FPDF else object):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(0, 180, 50)
        self.cell(0, 8, 'RAPTOR Intelligence System | CLASSIFICADO', align='R', new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 180, 50)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'RAPTOR v1.0 | Pag {self.page_no()}/{{nb}} | Documento Confidencial', align='C')


def gerar_pdf(d: DossieCompleto) -> str:
    if not HAS_FPDF:
        raise ImportError("fpdf2 nao instalado. Execute: pip install fpdf2")

    pdf = RaptorPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    nome = d.dados_operacionais.nome_grupo or d.empresa_alvo

    # Title
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(0, 180, 50)
    pdf.cell(0, 14, 'RAPTOR INTELLIGENCE REPORT', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Target name
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, f'Alvo: {nome}', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Score
    pdf.set_font('Helvetica', 'B', 14)
    score = d.sas_result.score
    if score >= 751:
        pdf.set_text_color(0, 180, 50)
    elif score >= 501:
        pdf.set_text_color(200, 180, 0)
    else:
        pdf.set_text_color(200, 60, 60)
    pdf.cell(0, 10, f'Score SAS: {score}/1000 - {d.sas_result.tier.value}', new_x="LMARGIN", new_y="NEXT")

    # Classification
    ha = d.dados_operacionais.hectares_total
    pdf.set_font('Helvetica', 'B', 12)
    if ha and ha < 5000:
        pdf.set_text_color(200, 60, 60)
        pdf.cell(0, 8, 'STATUS: ALVO DESCARTADO (BAIXO POTENCIAL < 5.000 ha)', new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_text_color(0, 180, 50)
        pdf.cell(0, 8, 'STATUS: ALVO CONFIRMADO - HIGH TICKET', new_x="LMARGIN", new_y="NEXT")

    if d.sas_result.recomendacao_comercial:
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 6, f'Recomendacao: {d.sas_result.recomendacao_comercial}', new_x="LMARGIN", new_y="NEXT")

    # Metadata
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f'Gerado: {d.timestamp_geracao} | Tempo: {d.tempo_total_segundos:.0f}s', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Raio-X
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 8, 'RAIO-X DA OPERACAO', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    op = d.dados_operacionais
    fi = d.dados_financeiros
    for l in [
        f"Area: {op.hectares_total:,} ha | Fazendas: {op.numero_fazendas}",
        f"Culturas: {', '.join(op.culturas)}",
        f"Regioes: {', '.join(op.regioes_atuacao)}",
        f"Funcionarios: {fi.funcionarios_estimados:,} | Capital: R${fi.capital_social_estimado/1e6:.1f}M",
    ]:
        pdf.cell(0, 6, l, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Score Breakdown
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 8, 'SCORE BREAKDOWN', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    b = d.sas_result.breakdown
    for l in [
        f"Musculo (Porte): {b.musculo}/400",
        f"Complexidade: {b.complexidade}/250",
        f"Gente (Gestao): {b.gente}/200",
        f"Momento (Gov/Tech): {b.momento}/150",
    ]:
        pdf.cell(0, 6, l, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Movimentos financeiros
    if fi.movimentos_financeiros:
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_text_color(30, 30, 80)
        pdf.cell(0, 8, 'MOVIMENTOS FINANCEIROS', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        for m in fi.movimentos_financeiros[:10]:
            txt = str(m)[:120]
            pdf.multi_cell(0, 5, f'  > {txt}', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # Decisores
    decs = d.decisores.get('decisores', []) if d.decisores else []
    if decs:
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_text_color(30, 30, 80)
        pdf.cell(0, 8, 'DECISORES-CHAVE', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        for dec in decs[:8]:
            nome_d = dec.get('nome', '')
            cargo = dec.get('cargo', '')
            rel = dec.get('relevancia_erp', '')
            pdf.cell(0, 5, f'  [{rel.upper()}] {nome_d} - {cargo}', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # Tech Stack
    ts = d.tech_stack or {}
    if ts:
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_text_color(30, 30, 80)
        pdf.cell(0, 8, 'TECH STACK DETECTADO', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(50, 50, 50)
        erp = ts.get('erp_principal', {})
        pdf.cell(0, 6, f'ERP: {erp.get("sistema","N/I")} | Maturidade TI: {ts.get("nivel_maturidade_ti","N/I")}', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # Secoes de analise
    for sec in d.secoes_analise:
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(0, 180, 50)
        pdf.cell(0, 10, f'{sec.icone} {sec.titulo}', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(40, 40, 40)
        clean = sec.conteudo.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5.5, clean)

    # Quality Gate
    if d.quality_report:
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(30, 30, 80)
        pdf.cell(0, 10, 'QUALITY GATE', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 6, f'Score: {d.quality_report.score_qualidade:.0f}% | Nivel: {d.quality_report.nivel.value}', new_x="LMARGIN", new_y="NEXT")
        for ch in d.quality_report.checks:
            ic = "[OK]" if ch.passou else "[FALHA]"
            pdf.cell(0, 5, f'  {ic} {ch.criterio} — {ch.nota}', new_x="LMARGIN", new_y="NEXT")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmp.name)
    return tmp.name
