"""
utils/pdf_export.py — Exportacao de dossie para PDF
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
    FPDF = object  # placeholder


class DossiePDF(FPDF if HAS_FPDF else object):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'Senior Scout 360 | Confidencial', align='R', new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pag {self.page_no()}/{{nb}}', align='C')


def gerar_pdf(d: DossieCompleto) -> str:
    if not HAS_FPDF:
        raise ImportError("fpdf2 nao instalado. Execute: pip install fpdf2")
    pdf = DossiePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(30, 30, 80)
    nome = d.dados_operacionais.nome_grupo or d.empresa_alvo
    pdf.cell(0, 12, f'Dossie: {nome}', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, f'Score SAS 4.0: {d.sas_result.score}/1000 - {d.sas_result.tier.value}', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f'Gerado: {d.timestamp_geracao} | Modelo: {d.modelo_usado} | Tempo: {d.tempo_total_segundos:.0f}s', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 8, 'Raio-X da Operacao', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    op = d.dados_operacionais
    fi = d.dados_financeiros
    for l in [f"Area: {op.hectares_total:,} ha | Fazendas: {op.numero_fazendas}",
              f"Culturas: {', '.join(op.culturas)}",
              f"Regioes: {', '.join(op.regioes_atuacao)}",
              f"Funcionarios: {fi.funcionarios_estimados:,} | Capital: R${fi.capital_social_estimado/1e6:.1f}M"]:
        pdf.cell(0, 6, l, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    if fi.movimentos_financeiros:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(30, 30, 80)
        pdf.cell(0, 8, 'Movimentos Financeiros', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        for m in fi.movimentos_financeiros:
            pdf.multi_cell(0, 5, f'  - {m}', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
    for sec in d.secoes_analise:
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(30, 30, 80)
        pdf.cell(0, 10, f'{sec.icone} {sec.titulo}', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(40, 40, 40)
        clean = sec.conteudo.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5.5, clean)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmp.name)
    return tmp.name
