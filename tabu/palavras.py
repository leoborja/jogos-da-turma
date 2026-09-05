#!/usr/bin/env python3
"""
palavras.py — as listas fechadas do Tabu.

O baralho NÃO é escrito à mão: as palavras-chave saem de uma lista de
frequência do português falado e as proibidas saem do artigo da Wikipédia.
O que mora aqui é só o que nenhuma base resolve sozinha — palavra de função,
palavra de meta-texto de enciclopédia, e os vetos que sobraram da revisão.
"""

# --------------------------------------------------------------- função
# Classe fechada do português. O Wikcionário lista várias delas como
# "substantivo" ("como", "mais", "este"), então o filtro de classe não basta.
FUNCAO = set("""
a o as os um uma uns umas de do da dos das em no na nos nas por pelo pela pelos
pelas para com sem sob sobre entre ante apos ate desde contra perante durante
mediante conforme segundo e ou mas nem porem contudo todavia entretanto logo
pois porque porquanto que se como quando onde aonde quanto qual quais quem cujo
cuja cujos cujas ja nao sim tambem ainda apenas somente so mesmo assim entao
antes depois hoje ontem amanha agora sempre nunca jamais talvez alias inclusive
eu tu voce ele ela nos vos eles elas me te lhe nos vos lhes meu minha teu tua
seu sua nosso nossa vosso vossa este esta isto esse essa isso aquele aquela
aquilo tal tais cada todo toda todos todas outro outra outros outras algum
alguma alguns algumas nenhum nenhuma ambos ambas muito muita muitos muitas
pouco pouca poucos poucas tanto tanta tantos tantas varios varias diversos
diversas certo certa qualquer quaisquer proprio propria proprios proprias
mais menos maior menor melhor pior bastante demais bem mal
um dois tres quatro cinco seis sete oito nove dez onze doze treze quinze vinte
trinta quarenta cinquenta sessenta setenta oitenta noventa cem cento mil milhao
milhoes bilhao primeiro primeira segundo segunda terceiro terceira quarto
quarta quinto quinta sexto sexta setimo oitavo nono decimo meio meia metade
dentro fora perto longe acima abaixo atras frente cima baixo lado longo largo
""".split())

# --------------------------------------------------------------- verbo comum
# Formas conjugadas que o Wikcionário registra também como substantivo.
VERBAIS = set("""
ser estar ter haver ir vir dar ver saber querer dizer fazer poder dever ficar
passar chegar levar trazer pegar deixar achar olhar falar andar entrar sair
voltar viver morrer comer beber usar criar tornar seguir manter existir
sendo sido feito feita feitos feitas dado dada dados dadas visto vista posto
posta dito dita usado usada usados usadas chamado chamada chamados chamadas
conhecido conhecida encontrado encontrada considerado considerada realizado
realizada formado formada composto composta utilizado utilizada apresentado
denominado denominada destinado destinada situado situada obtido obtida
produzido produzida constituido constituida desenvolvido desenvolvida
""".split())

# --------------------------------------------------------------- meta-texto
# Vocabulário de enciclopédia: aparece no artigo por ser artigo, não por ser
# o assunto. Etimologia, gentílico, unidade, nota de fonte.
META = set("""
lingua linguas idioma idiomas portugues portuguesa brasileiro brasileira
europeu europeia ingles inglesa latim latina latino grego grega frances
francesa espanhol espanhola alemao alema italiano italiana arabe japones
chines russo americano americana ocidental oriental
palavra palavras termo termos nome nomes designacao denominacao origem
etimologia sentido significado conceito definicao acepcao sinonimo variante
seculo seculos ano anos ano decada epoca periodo era data hora horas minuto
minutos dia dias semana mes meses
pais paises regiao regioes mundo mundial estado estados cidade cidades
municipio provincia continente nacional internacional local global
autor autores obra obras livro livros artigo artigos texto fonte fontes
pagina paginas titulo capitulo edicao publicacao referencia nota
estudo estudos pesquisa pesquisas dados dado analise resultado resultados
teoria hipotese metodo metodologia
tipo tipos forma formas modo maneira jeito caso casos exemplo exemplos
parte partes area areas nivel niveis valor valores numero numeros quantidade
grupo grupos conjunto conjuntos serie series classe classes categoria
processo processos sistema sistemas modelo modelos estrutura funcao
elemento elementos aspecto aspectos respeito relacao situacao condicao
posicao questao ponto pontos lugar lugares coisa coisas vez vezes
membro membros especie especies genero familia ordem reino
populacao habitante habitantes total media maioria minoria percentual
metro metros centimetro milimetro quilometro quilo grama litro tonelada
quadrado cubico graus celsius unidade medida
comum comuns geral gerais geralmente normalmente principalmente atualmente
antigamente posteriormente anteriormente inicialmente finalmente
principal principais secundario diferente diferentes semelhante similar
grande grandes pequeno pequena novo nova velho velha antigo antiga moderno
alto alta baixo baixa unico unica variado variada natural naturais artificial
central anual mensal diario possivel necessario importante conhecido
""".split())

# --------------------------------------------------------------- vetos
# Palavras que a mineração encontra mas que não viram carta boa: ou o artigo
# fala de outra coisa, ou a palavra é abstrata demais pra alguém descrever.
# Cada veto foi visto na revisao.csv antes de entrar aqui.
VETADAS_CHAVE = set("""
coisa gente jeito tanto tudo nada algo negocio troco troca bagulho parada
vez volta hora tempo momento instante ocasiao
verdade mentira certeza duvida talvez razao motivo causa efeito
questao assunto tema ponto detalhe fato dado caso exemplo
parte pedaco metade dobro resto total soma conta numero
lado frente costas fundo meio centro topo base beira canto
forma formato maneira modo estilo tipo especie genero categoria
nivel grau ordem serie sequencia etapa fase estagio
valor preco custo taxa juro renda lucro margem
uso funcao papel cargo posto posicao lugar espaco
grupo turma equipe time bando monte punhado
inicio comeco fim final termino
sorte azar chance risco perigo problema solucao
senhor senhora dona moco rapaz sujeito cara pessoa individuo
deus diabo inferno ceu alma espirito
palavra frase termo nome sobrenome apelido titulo
lista objetivo futuro passado presente confianca competicao acordo mama calado
interesse esforco atencao cuidado respeito vontade opiniao evidencia
""".split())

# Palavrão, xingamento e assunto pesado. A lista de frequência vem de legenda
# de filme, então isso aparece; numa mesa de amigos, não rende carta — rende
# constrangimento. Fora da mesa por decisão, não por dado.
PESADAS = set("""
vadia puta putas piranha vagabunda cadela biscate rapariga
caralho porra buceta cu cuzao foda fodido merda bosta viado bicha
sapatao traveco crioulo macaco preta retardado mongoloide aleijado
suicidio estupro estuprador pedofilia aborto incesto
overdose heroina cocaina maconha crack baseado metanfetamina
prostituicao prostituta bordel genocidio holocausto herpes gonorreia sifilis
penis vagina vulva clitoris testiculo esperma orgasmo masturbacao
sexo lesbica gay heterossexual travesti transexual
""".split())
VETADAS_CHAVE |= PESADAS

# Palavras que nunca devem virar PROIBIDA, mesmo pontuando alto. Duas famílias:
# (a) vazias demais pra travar quem descreve;
# (b) formas verbais que o Wikcionário também registra como substantivo
#     ("leva", "toma", "percebe", "torno") — o filtro de classe deixa passar.
VETADAS_PROIBIDA = set("""
pessoa pessoas gente individuo objeto material item peca
espaco ambiente sitio acao atividade pratica
caracteristica propriedade qualidade capacidade
importancia presenca ausencia existencia extensao
leva levam toma tomam torno torna percebe percebem chega chegam passa passam
fica ficam deixa deixam mostra mostram conta contam trata tratam apresenta
serve servem parte partem volta voltam segue seguem cria criam gera geram
carrega leve dispoe disposto disposta mesma mesmo maiores menores suficiente
imediato delicada novidade astro alfa socio virtude juizes atriz cobre
nada deve gira perca vulgar boa boas inves carater permanente momento passo
gen figura contexto laco extrema perfil sujeito
""".split())

VETADAS_PROIBIDA |= PESADAS
