"""
utils/export_handler.py — Gerador de Relatórios (PDF/JSON)
Adaptado para Protocolo Bruno Lima (Relatório Forense Ciro)
"""
import json
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

class ExportHandler:
    def __init__(self):
        self.width, self.height = A4

    def gerar_json(self, dossie: dict) -> bytes:
        """Exporta o dossiê completo em JSON."""
        return json.dumps(dossie, indent=2, ensure_ascii=False).encode('utf-8')

    def gerar_pdf(self, dossie: dict) -> bytes:
        """Gera PDF Executivo com Design Profissional."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Página 1: Capa e Indicadores
        self._pagina_capa(c, dossie)
        
        # Página 2: Análise Estratégica (O Relatório Ciro)
        self._adicionar_analise_estrategica(c, dossie)
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    def _cabecalho_padrao(self, c, dossie, titulo_pag="INTELLIGENCE REPORT"):
        """Cabeçalho padrão para todas as páginas."""
        # Faixa superior
        c.setFillColor(colors.darkblue)
        c.rect(0, self.height - 50, self.width, 50, fill=True, stroke=False)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(30, self.height - 35, f"RADAR FOX-3 | {titulo_pag}")
        
        # Subtítulo com Data e Alvo
        data_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        sas_score = dossie.get('sas_score', 'N/A')
        sas_tier = dossie.get('sas_tier', 'N/A')
        
        subtitulo = f"ALVO: {dossie.get('empresa_alvo', 'ALVO DESCONHECIDO')} | SCORE SAS: {sas_score} ({sas_tier}) | DATA: {data_str}"
        c.setFont("Helvetica", 9)
        c.drawString(30, self.height - 48, subtitulo)

    def _pagina_capa(self, c, dossie):
        """Página 1: Resumo Executivo."""
        self._cabecalho_padrao(c, dossie)
        
        y = self.height - 100
        
        # Indicadores Principais (Cards)
        dados_ops = dossie.get('dados_operacionais', {})
        dados_fin = dossie.get('dados_financeiros', {})
        tech = dossie.get('tech_stack', {})
        
        indicadores = [
            ("Área Total", f"{dados_ops.get('area_total', 0):,.0f} ha"),
            ("Faturamento", str(dados_fin.get('faturamento_estimado', 'N/D'))[:30]), # Limita tamanho
            ("ERP Principal", str(tech.get('erp_principal', 'N/D')))
        ]
        
        # Desenha "Cartões"
        x_start = 50
        for titulo, valor in indicadores:
            c.setStrokeColor(colors.lightgrey)
            c.rect(x_start, y - 60, 150, 50, stroke=True, fill=False)
            
            c.setFillColor(colors.grey)
            c.setFont("Helvetica", 10)
            c.drawString(x_start + 10, y - 25, titulo)
            
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 12)
            # Ajusta fonte se valor for longo
            if len(str(valor)) > 15:
                c.setFont("Helvetica-Bold", 9)
            c.drawString(x_start + 10, y - 45, str(valor))
            
            x_start += 170

        y -= 100
        
        # Detalhes Operacionais
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "DETALHES OPERACIONAIS & INDUSTRIAIS")
        y -= 20
        c.line(50, y, 550, y)
        y -= 20
        
        c.setFont("Helvetica", 10)
        ind = dados_ops.get('detalhes_industriais', {})
        if ind:
            details = [
                f"Armazenagem: {ind.get('capacidade_armazenagem', 'N/D')}",
                f"Plantas: {', '.join(ind.get('plantas_industriais', [])[:3])}", # Max 3
                f"Segmentos: {', '.join(ind.get('segmentos_atuacao', []))}"
            ]
        else:
            details = ["Nenhuma infraestrutura industrial pública identificada."]
            
        for d in details:
            c.drawString(50, y, f"• {d}")
            y -= 15

        y -= 20
        
        # Decisores
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "DECISORES & CAPEX")
        y -= 20
        c.line(50, y, 550, y)
        y -= 20
        
        c.setFont("Helvetica", 10)
        org = dossie.get('dados_organizacionais', {})
        people = org.get('decisores_chave', {})
        
        if people:
            diretoria = people.get('diretoria', [])[:3]
            for p in diretoria:
                c.drawString(50, y, f"• {p}")
                y -= 15
        else:
            c.drawString(50, y, "• Organograma não disponível publicamente.")

        c.showPage()

    def _adicionar_analise_estrategica(self, c, dossie):
        """Página 2: O Relatório Forense (Protocolo Bruno Lima)."""
        self._cabecalho_padrao(c, dossie, "ANÁLISE ESTRATÉGICA FORENSE")
        
        y = self.height - 80
        margin = 50
        max_width = self.width - 2 * margin
        
        # Tenta pegar o texto do Ciro
        texto_ciro = dossie.get("analise_estrategica", {}).get("relatorio_completo_ciro", "")
        
        # Fallback se não tiver Ciro
        if not texto_ciro:
            texto_ciro = "Relatório Forense indisponível. Consulte a versão web."

        # Processamento de Texto para PDF (Quebra de Linha Básica)
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        
        lines = texto_ciro.split('\n')
        
        for line in lines:
            # Tratamento básico de Markdown
            is_bold = "**" in line or "##" in line
            clean_line = line.replace("**", "").replace("## ", "").replace("# ", "").replace("🕵️‍♂️", "").replace("🧬", "")
            
            if is_bold:
                c.setFont("Helvetica-Bold", 10)
                y -= 5 # Extra space before header
            else:
                c.setFont("Helvetica", 10)
            
            # Word wrap manual
            words = clean_line.split()
            current_line = ""
            
            for word in words:
                test_line = f"{current_line} {word}".strip()
                width = c.stringWidth(test_line, "Helvetica-Bold" if is_bold else "Helvetica", 10)
                
                if width < max_width:
                    current_line = test_line
                else:
                    c.drawString(margin, y, current_line)
                    y -= 14
                    current_line = word
                    
                    # Nova página se acabar espaço
                    if y < 50:
                        c.showPage()
                        self._cabecalho_padrao(c, dossie, "ANÁLISE FORENSE (CONT.)")
                        y = self.height - 80
            
            # Imprime o resto da linha
            if current_line:
                c.drawString(margin, y, current_line)
                y -= 14
                
            # Nova página se acabar espaço
            if y < 50:
                c.showPage()
                self._cabecalho_padrao(c, dossie, "ANÁLISE FORENSE (CONT.)")
                y = self.height - 80
