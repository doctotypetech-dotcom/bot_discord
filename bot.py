#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import discord
from discord.ext import commands
import random
import re
import os
import sys
import time
from collections import defaultdict, Counter
from datetime import datetime

# =====================================================
# CHATBOT AVEC LONGUEUR MINIMALE DE PHRASE (7 mots par défaut)
# =====================================================

class PhraseMarkovBot:
    """Chatbot à chaîne de Markov avec contrôle de la longueur des phrases"""
    
    def __init__(self, corpus_files, min_words=7, max_words=20):
        self.min_words = min_words
        self.max_words = max_words
        self.transitions = defaultdict(Counter)
        self.start_words = []
        self.cache = []
        self.load_corpora(corpus_files)
        # Pré-générer un cache de phrases en respectant la longueur minimale
        self.cache = [self.generate_sentence_valid_length() for _ in range(30)]
    
    def split_phrases(self, text):
        """Découpe un texte en phrases"""
        pattern = r'([^.!?]+(?:\.\.\.|[.!?]))\s*'
        phrases = re.findall(pattern, text)
        return [p.strip() for p in phrases if p.strip()]
    
    def tokenize(self, phrase):
        return phrase.lower().split()
    
    def load_corpora(self, corpus_files):
        """Charge un ou plusieurs fichiers corpus"""
        all_phrases = []
        for corpus_file in corpus_files:
            if os.path.exists(corpus_file):
                print(f"📖 Chargement de {corpus_file}...")
                with open(corpus_file, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                phrases = self.split_phrases(raw_text)
                all_phrases.extend(phrases)
                print(f"   → {len(phrases)} phrases extraites")
            else:
                print(f"⚠️ Fichier {corpus_file} introuvable, ignoré.")
        
        if not all_phrases:
            print("⚠️ Aucun fichier corpus valide trouvé. Utilisation d'un corpus minimal.")
            default_text = "Le bot est prêt. Bonjour tout le monde. Comment ça va ? Le soleil brille. La banquise fond. Le capitaine Nemo regarde l'horizon."
            all_phrases = self.split_phrases(default_text)
        
        print(f"📖 Total: {len(all_phrases)} phrases chargées.")
        
        all_tokens = []
        for phrase in all_phrases:
            tokens = self.tokenize(phrase)
            if len(tokens) < 1:
                continue
            tokens_with_markers = ['<START>'] + tokens + ['<END>']
            all_tokens.extend(tokens_with_markers)
            if tokens:
                self.start_words.append(tokens[0])
        
        if not all_tokens:
            print("⚠️ Aucune phrase valide trouvée.")
            return
        
        for i in range(len(all_tokens) - 1):
            current = all_tokens[i]
            next_word = all_tokens[i + 1]
            self.transitions[current][next_word] += 1
        
        self.start_words = list(set(self.start_words))
        print(f"🔗 {len(self.transitions)} états, {len(self.start_words)} mots de départ.")
        print(f"📏 Longueur des phrases : min {self.min_words} mots, max {self.max_words} mots")
    
    def weighted_choice(self, counter):
        if not counter:
            return None
        total = sum(counter.values())
        r = random.random() * total
        cumul = 0
        for word, weight in counter.items():
            cumul += weight
            if r < cumul:
                return word
        return list(counter.keys())[-1]
    
    def generate_sentence(self, max_words=None):
        """Génère une phrase sans garantie de longueur"""
        if not self.start_words:
            return "Le cerveau du bot est vide."
        
        if max_words is None:
            max_words = self.max_words
        
        current = random.choice(self.start_words)
        sentence = [current]
        
        for _ in range(max_words - 1):
            next_words = self.transitions.get(current, {})
            if not next_words:
                break
            next_word = self.weighted_choice(next_words)
            if not next_word or next_word == '<END>':
                break
            sentence.append(next_word)
            current = next_word
        
        result = " ".join(sentence)
        if result:
            result = result[0].upper() + result[1:]
        if not re.search(r'[.!?…]$', result):
            result += '.'
        
        return result
    
    def generate_sentence_valid_length(self):
        """Génère une phrase qui respecte la longueur minimale"""
        max_attempts = 30
        for _ in range(max_attempts):
            sentence = self.generate_sentence()
            word_count = len(sentence.split())
            if word_count >= self.min_words:
                return sentence
        # Si on n'y arrive pas, on retourne la plus longue possible
        return self.generate_sentence(max_words=self.max_words)
    
    def respond(self, user_input=None):
        """Génère une réponse depuis le cache ou en génère une nouvelle"""
        # Renouvelle le cache de temps en temps
        if random.random() < 0.05:
            self.cache.pop(0)
            self.cache.append(self.generate_sentence_valid_length())
        return random.choice(self.cache)


# =====================================================
# LECTURE DU TOKEN DEPUIS token.txt
# =====================================================

def read_token(token_file="token.txt"):
    if not os.path.exists(token_file):
        print(f"❌ Fichier {token_file} introuvable !")
        print("Crée un fichier token.txt avec ton token Discord à l'intérieur.")
        sys.exit(1)
    
    with open(token_file, 'r', encoding='utf-8') as f:
        token = f.read().strip()
    
    if not token:
        print("❌ Le fichier token.txt est vide !")
        sys.exit(1)
    
    return token


# =====================================================
# CONFIGURATION
# =====================================================

# Liste des fichiers corpus (phr.txt ET phrases.txt)
CORPUS_FILES = []
if os.path.exists("phr.txt"):
    CORPUS_FILES.append("phr.txt")
if os.path.exists("phrases.txt"):
    CORPUS_FILES.append("phrases.txt")

if not CORPUS_FILES:
    print("⚠️ Aucun fichier corpus trouvé (phr.txt ou phrases.txt)")
    print("   Création d'un fichier phr.txt par défaut...")
    with open("phr.txt", "w", encoding="utf-8") as f:
        f.write("Bonjour tout le monde.\nComment ça va aujourd'hui ?\nLe bot est prêt à discuter.\nLe capitaine Nemo navigue sous la banquise.\n")
    CORPUS_FILES.append("phr.txt")

TOKEN = read_token("token.txt")

# Paramètres de longueur des phrases (7 mots minimum par défaut)
MIN_WORDS = 7    # Nombre minimum de mots par phrase
MAX_WORDS = 20   # Nombre maximum de mots par phrase

print("🤖 Initialisation du MarkovBot...")
print(f"📁 Fichiers corpus: {', '.join(CORPUS_FILES)}")
print(f"📁 Fichier token: token.txt")
chatbot = PhraseMarkovBot(CORPUS_FILES, min_words=MIN_WORDS, max_words=MAX_WORDS)

# Configuration des intents Discord
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionnaire pour suivre la dernière activité des utilisateurs
last_activity = {}
INACTIVITY_THRESHOLD = 1800  # 30 minutes

# ===== SALON AUTORISÉ SUR LES SERVEURS =====
# Le bot ne répondra que dans ce salon (sur les serveurs)
# En MP, il répond toujours
ALLOWED_CHANNEL_NAME = "ia_2000"  # Nom exact du salon (insensible à la casse)


# =====================================================
# COMMANDES
# =====================================================

@bot.command(name='marco')
async def marco_command(ctx):
    """!marco - génère une phrase aléatoire (7+ mots)"""
    async with ctx.typing():
        response = chatbot.generate_sentence_valid_length()
    await ctx.send(response)
    last_activity[ctx.author.id] = time.time()


@bot.command(name='marco_long')
async def marco_long_command(ctx):
    """!marco_long - génère une phrase plus longue"""
    async with ctx.typing():
        old_max = chatbot.max_words
        chatbot.max_words = 30
        response = chatbot.generate_sentence_valid_length()
        chatbot.max_words = old_max
    await ctx.send(response)
    last_activity[ctx.author.id] = time.time()


@bot.command(name='marco_short')
async def marco_short_command(ctx):
    """!marco_short - force une phrase courte (ignore la contrainte min)"""
    async with ctx.typing():
        response = chatbot.generate_sentence(max_words=8)
    await ctx.send(response)
    last_activity[ctx.author.id] = time.time()


@bot.command(name='marco_stats')
async def stats_command(ctx):
    """Affiche les statistiques du bot"""
    embed = discord.Embed(
        title="📊 Statistiques du MarkovBot",
        color=0x00ff00
    )
    embed.add_field(name="États Markov", value=str(len(chatbot.transitions)), inline=True)
    embed.add_field(name="Mots de départ", value=str(len(chatbot.start_words)), inline=True)
    embed.add_field(name="Taille du cache", value=str(len(chatbot.cache)), inline=True)
    embed.add_field(name="Mots min par phrase", value=str(chatbot.min_words), inline=True)
    embed.add_field(name="Mots max par phrase", value=str(chatbot.max_words), inline=True)
    embed.add_field(name="Salon autorisé", value=f"#{ALLOWED_CHANNEL_NAME} (serveurs) / MP", inline=True)
    
    # Afficher un exemple de phrase
    example = chatbot.generate_sentence_valid_length()
    embed.add_field(name="📝 Exemple", value=f"*{example[:100]}*", inline=False)
    
    await ctx.send(embed=embed)
    last_activity[ctx.author.id] = time.time()


@bot.command(name='marco_help')
async def help_command(ctx):
    """Affiche l'aide"""
    help_text = f"""
**🤖 MarkovBot - Aide**

**Fonctionnement :**
- Sur les serveurs : répond UNIQUEMENT dans `#{ALLOWED_CHANNEL_NAME}`
- En MP : répond à TOUS les messages

**Commandes :**
- `!marco` : Génère une phrase aléatoire (7 mots minimum)
- `!marco_long` : Génère une phrase plus longue
- `!marco_short` : Force une phrase courte
- `!marco_stats` : Affiche les statistiques
- `!marco_help` : Affiche cette aide
- `!marco_reload` : Recharge les fichiers corpus (phr.txt et phrases.txt)
- `!+ <titre du livre>` : Propose un livre à ajouter au corpus

**Fichiers utilisés :**
- `phr.txt` : ton premier corpus
- `phrases.txt` : ton second corpus (les deux sont fusionnés)
- `token.txt` : ton token Discord
- `suggestions.log` : suggestions de livres

**Astuce :** Si tu reviens après un long moment, je te rappellerai l'existence de `!help` 😉
    """
    await ctx.send(help_text)
    last_activity[ctx.author.id] = time.time()


@bot.command(name='marco_reload')
async def reload_command(ctx):
    """!marco_reload - recharge les fichiers corpus"""
    async with ctx.typing():
        corpus_files = []
        if os.path.exists("phr.txt"):
            corpus_files.append("phr.txt")
        if os.path.exists("phrases.txt"):
            corpus_files.append("phrases.txt")
        
        if not corpus_files:
            await ctx.send("❌ Aucun fichier corpus trouvé (phr.txt ou phrases.txt)")
            return
        
        global chatbot, MIN_WORDS, MAX_WORDS
        chatbot = PhraseMarkovBot(corpus_files, min_words=MIN_WORDS, max_words=MAX_WORDS)
        await ctx.send(f"✅ Corpus rechargé ! {len(corpus_files)} fichier(s) chargé(s), {len(chatbot.transitions)} états Markov.")
    last_activity[ctx.author.id] = time.time()


@bot.command(name='+')
async def suggest_book_command(ctx, *, book_title=""):
    """!+ <n'importe quoi> - propose un livre ou n'importe quelle suggestion au corpus"""
    
    # Si aucun texte n'est fourni, on utilise un message par défaut
    if not book_title or book_title.strip() == "":
        book_title = "[suggestion vide]"
    
    # Récupère les infos (avec gestion des DM)
    author_name = ctx.author.name
    author_display = ctx.author.display_name
    
    # Gestion du salon (les DM n'ont pas de .name)
    if ctx.guild:
        channel_name = f"#{ctx.channel.name}"
        guild_name = ctx.guild.name
    else:
        channel_name = "MP (message privé)"
        guild_name = "Message Privé"
    
    # Prépare le message de notification
    notification = f"""📚 NOUVELLE SUGGESTION !
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Utilisateur : {author_name} ({author_display})
📌 Salon : {channel_name}
🏠 Serveur : {guild_name}
💬 Suggestion : {book_title}
🕐 Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    # Écrit dans le fichier de log
    log_file = "suggestions.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{notification}\n\n")
    
    # Affichage dans le terminal du bot
    print(f"\n🔔 {notification}\n")
    
    # Envoie une notification système si possible (Linux)
    try:
        if os.environ.get('DISPLAY'):
            os.system(f'zenity --notification --text="Nouveau livre à ajouter : {notification}"')
        os.system(f'echo "📚 Suggestion: {book_title} (par {author_name})" | wall 2>/dev/null')
    except Exception as e:
        print(f"⚠️ Notification système échouée: {e}")
    
    # Réponse sur Discord
    await ctx.send(f"✅ Suggestion enregistrée !\n💬 *{book_title[:100]}*\n\nMerci pour ta contribution !")
    last_activity[ctx.author.id] = time.time()


# =====================================================
# RÉPONSE À TOUS LES MESSAGES
# =====================================================

@bot.event
async def on_ready():
    print(f"\n✅ {bot.user} est connecté à Discord !")
    print(f"📊 Stats : {len(chatbot.transitions)} transitions Markov")
    print(f"📁 Fichiers corpus : phr.txt, phrases.txt")
    print(f"📏 Phrases : minimum {MIN_WORDS} mots")
    print(f"⏰ Seuil d'inactivité : {INACTIVITY_THRESHOLD // 60} minutes")
    print(f"🔒 Salon autorisé sur les serveurs : #{ALLOWED_CHANNEL_NAME}")
    print(f"📝 Suggestions : fichier suggestions.log")
    print(f"👁️ Les logs apparaîtront dans ce terminal\n")


@bot.event
async def on_message(message):
    # Ignorer les messages du bot lui-même
    if message.author == bot.user:
        return
    
    # Gérer les commandes (les commandes fonctionnent partout)
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    # ===== RESTRICTION AU SALON ia_2000 UNIQUEMENT =====
    # Si c'est sur un serveur (et pas en message privé)
    if message.guild:
        # Vérifie si le salon s'appelle "ia_2000" (comparaison insensible à la casse)
        if message.channel.name.lower() != ALLOWED_CHANNEL_NAME.lower():
            # Pas dans le bon salon : on ignore complètement le message
            return
    # En MP (message.guild == None), on répond toujours, pas de restriction
    # ===== FIN DE LA RESTRICTION =====
    
    # Vérifier l'inactivité de l'utilisateur
    user_id = message.author.id
    current_time = time.time()
    show_help_reminder = False
    
    if user_id in last_activity:
        time_since_last = current_time - last_activity[user_id]
        if time_since_last > INACTIVITY_THRESHOLD:
            show_help_reminder = True
    else:
        # Premier message de cet utilisateur
        show_help_reminder = True
    
    # Mettre à jour l'activité
    last_activity[user_id] = current_time
    
    # Générer la réponse Markov
    response = chatbot.respond(message.content)
    
    # Ajouter un rappel !help si nécessaire
    if show_help_reminder:
        reminder = f"👋 **Astuce** : Tu peux taper `!help` pour voir les commandes disponibles ! (dernier message il y a plus de {INACTIVITY_THRESHOLD // 60} min)\n\n"
        final_response = reminder + response
    else:
        final_response = response
    
    # Affichage dans le terminal
    print("-" * 60)
    print(f"[{datetime.now().strftime('%H:%M:%S')}]")
    if message.guild:
        print(f"🏠 Serveur: {message.guild.name} | Salon: #{message.channel.name}")
    else:
        print(f"💬 MP de: {message.author.name}")
    print(f"👤 {message.author.name} a envoyé : {message.content[:100]}")
    print(f"🤖 Réponse du bot : {response[:100]}")
    if show_help_reminder:
        print(f"💡 Rappel !help envoyé (inactivité > {INACTIVITY_THRESHOLD // 60} min)")
    print("-" * 60)
    
    # Envoyer la réponse
    async with message.channel.typing():
        await message.channel.send(final_response)


# =====================================================
# LANCEMENT
# =====================================================

if __name__ == "__main__":
    print("🚀 Lancement du bot Discord...")
    print("=" * 40)
    bot.run(TOKEN)
