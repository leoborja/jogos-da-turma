# -*- coding: utf-8 -*-
"""
Nota de mesa de cada indicador: o que o número mede, em português e em uma
frase, com a pegadinha quando existe.

Escritas a partir da definição oficial que a API do Banco Mundial devolve em
`sourceNote`. A definição original vai junto no banco.json, palavra por
palavra, pra quem quiser conferir — estas notas são o resumo que o juiz lê em
voz alta, não a fonte.

Regra pra escrever nota nova: dizer o que ENTRA e o que FICA DE FORA. É quase
sempre a exclusão que gera briga na mesa.
"""

NOTAS = {
    # ---------------- economia e comércio ----------------
    "NE.EXP.GNFS.CD": "Bens e serviços vendidos a não residentes, a preço do próprio ano. Serviço conta junto com mercadoria.",
    "NE.IMP.GNFS.CD": "Bens e serviços comprados de não residentes, a preço do próprio ano.",
    "NY.GDP.MKTP.CD": "Toda a renda gerada produzindo no território, em dólar do ano — sem corrigir inflação nem diferença de preço entre países.",
    "NY.GDP.PCAP.CD": "PIB dividido pela população, em dólar do ano. Não corrige o fato de a vida custar mais em uns países que em outros.",
    "NY.GDP.PCAP.PP.CD": "PIB por habitante convertido por paridade de poder de compra: aqui a diferença de preço entre países ESTÁ corrigida.",
    "NY.GDP.MKTP.KD.ZG": "Variação do PIB em relação ao ano anterior, a preço constante de 2015.",
    "FP.CPI.TOTL.ZG": "Variação anual do custo de uma cesta de consumo — o IPCA de cada país.",
    "FI.RES.TOTL.CD": "Ativos externos que o banco central controla e pode usar na hora, ouro monetário incluído.",
    "BX.KLT.DINV.CD.WD": "Entrada de capital de quem compra ao menos 10% de uma empresa — controle ou influência, não aplicação financeira.",
    "BX.TRF.PWKR.CD.DT": "Dinheiro que emigrantes mandam pra casa, mais salário de trabalhador de fronteira e sazonal.",
    "NE.TRD.GNFS.ZS": "Exportação mais importação, dividido pelo PIB. Passa de 100% sem erro nenhum: quem reexporta movimenta mais do que produz.",
    "TX.VAL.MRCH.CD.WT": "Só mercadoria. Serviço, ouro não monetário e turismo ficam de fora.",
    "TX.VAL.TECH.CD": "Produtos de alta intensidade em pesquisa: aeroespacial, computador, farmacêutico, instrumento científico e máquina elétrica.",
    "GC.TAX.TOTL.GD.ZS": "Só tributo do governo central. Imposto de estado e município pode ficar de fora, o que derruba alguns países injustamente.",
    "DT.DOD.DECT.CD": "Dívida com não residentes. Só país de renda baixa e média entra no levantamento — por isso não tem rico na lista.",
    "SI.POV.GINI": "0 seria todo mundo ganhando igual, 100 seria uma pessoa ficando com tudo. Uns países medem renda, outros consumo.",
    "SL.UEM.TOTL.ZS": "Quem não tem trabalho mas está disponível e procurando. Quem desistiu de procurar sai da conta.",
    "SL.TLF.CACT.FE.ZS": "Mulheres de 15 anos ou mais que trabalham ou procuram trabalho, sobre o total de mulheres nessa idade.",
    "GC.DOD.TOTL.GD.ZS": "Estoque de dívida do governo central sobre o PIB. Nem todo país reporta, então a lista tem buraco.",
    "FR.INR.LEND": "Juro que o banco cobra do setor privado no curto e médio prazo. Cada país define de um jeito, então a comparação tem limite.",
    "CM.MKT.LCAP.GD.ZS": "Valor de mercado das empresas listadas sobre o PIB. Passa de 100% sem erro: bolsa não é fluxo, é estoque.",
    "GC.XPN.TOTL.GD.ZS": "Despesa do governo central sobre o PIB.",
    "SI.DST.10TH.10": "Fatia da renda (ou do consumo) que fica com os 10% do topo.",

    # ---------------- população e território ----------------
    "SP.POP.TOTL": "Todo mundo que mora no país, com documento ou sem. Estimativa de meio de ano.",
    "AG.SRF.TOTL.K2": "Área total, contando lago, rio e algumas águas costeiras.",
    "EN.POP.DNST": "População dividida pela área de TERRA — a água sai da conta.",
    "SP.URB.TOTL.IN.ZS": "O que é 'urbano' cada país define do seu jeito, então a comparação tem uma folga.",
    "SP.RUR.TOTL": "População total menos a urbana. O que é 'rural' cada país define.",
    "SP.POP.GROW": "Crescimento da população de um ano pro outro, com migração dentro.",
    "SP.DYN.TFRT.IN": "Quantos filhos uma mulher teria a vida toda se as taxas daquele ano valessem pra sempre.",
    "SP.POP.65UP.TO.ZS": "Fatia da população com 65 anos ou mais.",
    "SM.POP.TOTL": "Quem mora no país mas nasceu fora, refugiado incluído. É o estoque acumulado, não a entrada do ano.",
    "SP.DYN.CDRT.IN": "Mortes por mil habitantes no ano, sem ajustar por idade — país envelhecido aparece alto mesmo sendo saudável.",

    # ---------------- saúde ----------------
    "SP.DYN.LE00.IN": "Quantos anos um recém-nascido viveria se a mortalidade daquele ano nunca mudasse. Não é a idade média de quem morre hoje.",
    "SP.DYN.IMRT.IN": "Bebês que morrem antes de completar um ano, por mil nascidos vivos.",
    "SH.XPD.CHEX.PC.CD": "Gasto com saúde por habitante, público e privado somados. Obra, equipamento e estoque de vacina ficam de fora.",
    "SH.XPD.CHEX.GD.ZS": "Gasto com saúde sobre o PIB. Obra, máquina e estoque de vacina ficam de fora.",
    "SH.MED.PHYS.ZS": "Clínico geral e especialista.",
    "SH.MED.BEDS.ZS": "Leitos de internação em hospital público, privado, geral e especializado.",
    "SH.ALC.PCAP.LI": "Litros de álcool puro por pessoa de 15+ ao ano. Inclui bebida clandestina e desconta o que turista bebe.",
    "SH.PRV.SMOK": "Quem usa qualquer produto de tabaco, fumado ou não. Cigarro eletrônico não conta.",
    "SH.STA.OWGH.ME.ZS": "Crianças de até 5 anos com peso pra altura acima de dois desvios do padrão da OMS.",
    "SH.STA.SUIC.P5": "Mortes por suicídio por 100 mil habitantes, sem ajuste por idade. Quanto se subnotifica varia muito de país pra país.",
    "SH.DYN.NCOM.ZS": "Chance de quem tem 30 anos morrer antes dos 70 de doença do coração, câncer, diabetes ou respiratória crônica.",
    "SH.STA.TRAF.P5": "Mortes no trânsito por 100 mil habitantes — estimativa da OMS, não o registro oficial de cada país.",
    "SN.ITK.DEFC.ZS": "Quem come menos caloria do que precisa pra viver ativo e saudável. O valor 2,5 quer dizer 'abaixo de 2,5%'.",
    "SH.STA.STNT.ZS": "Crianças de até 5 anos com altura pra idade abaixo de dois desvios do padrão da OMS — sinal de desnutrição crônica.",
    "SH.H2O.BASW.ZS": "Água de fonte melhorada, a no máximo 30 minutos de ida e volta.",
    "SH.STA.BASS.ZS": "Banheiro melhorado que não é compartilhado com outra família.",
    "SP.ADO.TFRT": "Nascimentos por mil mulheres de 15 a 19 anos.",
    "SH.DYN.AIDS.ZS": "Fatia da população de 15 a 49 anos vivendo com HIV.",
    "SH.TBS.INCD": "Casos novos e recaídas por 100 mil habitantes, estimados pela OMS e recalculados todo ano.",
    "SH.IMM.MEAS": "Crianças de 12 a 23 meses que tomaram ao menos uma dose contra sarampo.",

    # ---------------- educação, ciência, tecnologia ----------------
    "SE.XPD.TOTL.GD.ZS": "Gasto do governo com educação sobre o PIB, contando dinheiro que veio de fora e passou pelo governo.",
    "SE.TER.ENRR": "Matriculados no superior sobre a população na idade típica. Matriculado de QUALQUER idade conta, por isso passa de 100%.",
    "SE.SEC.ENRR": "Matriculados no médio sobre a população na idade típica. Matriculado de qualquer idade conta.",
    "SE.ADT.LITR.ZS": "Quem tem 15 anos ou mais e consegue ler e escrever um texto simples do dia a dia.",
    "SE.COM.DURS": "Anos que a lei obriga a criança a ficar na escola.",
    "GB.XPD.RSDV.GD.ZS": "Pesquisa de empresa, governo, universidade e instituto sem fins lucrativos, tudo somado, sobre o PIB.",
    "SP.POP.SCIE.RD.P6": "Pesquisadores de P&D por milhão de habitantes.",
    "IP.PAT.RESD": "Pedidos de patente feitos por residentes. É pedido, não patente concedida.",
    "IT.NET.USER.ZS": "Quem usou internet nos últimos 3 meses, de qualquer aparelho e de qualquer lugar.",
    "IT.CEL.SETS.P2": "Linhas de celular por 100 habitantes. Passa de 100 fácil — muita gente tem dois chips.",
    "IT.NET.BBND.P2": "Assinaturas FIXAS de banda larga por 100 habitantes. Internet de celular não entra.",
    "SL.TLF.0714.ZS": "Crianças de 7 a 14 anos que trabalharam ao menos uma hora na semana da pesquisa.",

    # ---------------- energia, meio ambiente, agricultura ----------------
    "EG.ELC.ACCS.ZS": "Fatia da população com acesso a energia elétrica.",
    "EG.ELC.RNEW.ZS": "Fatia da ELETRICIDADE que sai de usina renovável. Hidrelétrica pesa muito aqui.",
    "EG.FEC.RNEW.ZS": "Renovável sobre TODO o consumo de energia, não só eletricidade. Lenha e carvão vegetal contam, o que sobe país pobre.",
    "EG.USE.PCAP.KG.OE": "Energia primária usada por habitante, em quilos equivalentes de petróleo.",
    "EG.IMP.CONS.ZS": "Importação menos exportação, dividido pelo consumo interno. O de baixo desconta o combustível abastecido em navio e avião de rota internacional, o de cima não — por isso Singapura e Panamá, os maiores portos de abastecimento do mundo, passam de 100%. Negativo seria exportador líquido.",
    "EN.GHG.CO2.PC.CE.AR5": "CO₂ de energia, indústria, agricultura e resíduo, por habitante. Desmatamento e uso da terra ficam de fora.",
    "EN.GHG.CO2.MT.CE.AR5": "CO₂ de energia, indústria, agricultura e resíduo. Desmatamento e uso da terra ficam de fora.",
    "AG.LND.FRST.ZS": "Mata natural ou plantada com árvore de 5 metros pra cima. Pomar, agrofloresta e parque urbano não contam.",
    "AG.LND.ARBL.ZS": "Lavoura temporária, horta e terra em pousio. Pomar e pasto permanente não entram.",
    "ER.PTD.TOTL.ZS": "Área protegida em terra e mar, de mil hectares pra cima, sobre a área total.",
    "AG.PRD.CREL.MT": "Cereal colhido pra grão seco. O que vira silagem ou pasto não conta.",
    "ER.H2O.FWTL.K3": "Água doce retirada no ano pra todo uso, sem contar a que evapora do reservatório.",
    "ER.H2O.INTR.PC": "Água de rio e lençol que NASCE dentro do país, por habitante. Rio que vem de fora não conta.",
    "AG.LND.PRCP.MM": "Média de longo prazo da chuva do ano, em milímetros.",
    "EN.ATM.PM25.MC.M3": "Exposição média a partícula fina PM2.5, ponderada por onde a população mora. Poeira de deserto conta junto com fumaça de indústria.",
    "SL.AGR.EMPL.ZS": "Quem trabalha em agricultura, caça, silvicultura ou pesca, sobre o total de ocupados.",
    "NV.IND.MANF.ZS": "Valor adicionado pela indústria de transformação sobre o PIB. Mineração e construção ficam de fora.",
    "NV.AGR.TOTL.ZS": "Valor adicionado por agricultura, silvicultura e pesca sobre o PIB.",
    "NY.GDP.PETR.RT.ZS": "Valor do petróleo produzido menos o custo de produzir, sobre o PIB.",
    "NY.GDP.MINR.RT.ZS": "Estanho, ouro, chumbo, zinco, ferro, cobre, níquel, prata, bauxita e fosfato: valor menos custo, sobre o PIB.",
    "TX.VAL.FUEL.ZS.UN": "Combustível mineral e lubrificante sobre tudo que o país exporta em mercadoria.",
    "TX.VAL.AGRI.ZS.UN": "Só matéria-prima agrícola BRUTA (fibra, madeira, borracha). Soja, minério e alimento processado não entram.",
    "AG.PRD.LVSK.XD": "Índice com base 100 na média de 2014-2016: mede o quanto a produção pecuária variou, não o tamanho dela.",

    # ---------------- transporte, turismo, segurança, política ----------------
    "ST.INT.ARVL": "Visitante que passa a noite. A mesma pessoa entrando duas vezes conta duas.",
    "ST.INT.RCPT.CD": "Gasto de visitante estrangeiro no país, incluindo passagem paga a companhia nacional.",
    "ST.INT.XPND.CD": "Gasto de residentes viajando pra fora, incluindo passagem paga a companhia estrangeira.",
    "IS.AIR.PSGR": "Passageiros de companhias REGISTRADAS no país, não importa de onde pra onde voaram — é por isso que a Irlanda aparece alto.",
    "IS.SHP.GOOD.TU": "Contêiner movimentado entre terra e mar. Transbordo conta duas vezes, e contêiner vazio também conta.",
    "IS.RRS.TOTL.KM": "Quilômetros de linha férrea em operação, de carga ou de passageiro.",
    "VC.IHR.PSRC.P5": "Morte causada de propósito, por 100 mil habitantes.",
    "MS.MIL.XPND.CD": "Gasto militar em dólar do ano, convertido pelo câmbio daquele ano.",
    "MS.MIL.XPND.GD.ZS": "Gasto militar sobre o PIB.",
    "MS.MIL.TOTL.P1": "Militar na ativa, com paramilitar junto quando ele dá pra substituir tropa regular. Reservista não conta.",
    "SG.GEN.PARL.ZS": "Cadeiras ocupadas por mulheres na câmara única ou na câmara baixa.",
    "BM.TRF.PWKR.CD.DT": "Dinheiro que sai do país mandado por imigrantes, mais salário de trabalhador de fronteira e sazonal.",
    "SM.POP.REFG": "Reconhecidos como refugiados pela Convenção de 1951, pelo ACNUR ou com proteção temporária.",
    "SM.POP.REFG.OR": "Refugiados que saíram desse país, contados onde quer que estejam hoje.",
    "IC.REG.DURS": "Dias corridos pra abrir uma empresa legalmente, pelo caminho mais rápido, custe o que custar.",
}
