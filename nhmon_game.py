"""Essai des monstres en jeu : NetHack lancé en mode wizard, dans un
panneau tmux à côté de l'éditeur quand c'est possible (le monstre y est
créé aussitôt par Ctrl-G), sinon en plein écran.

Mixin de l'éditeur : self.config, self.src, self.monsters, self.mon(),
self.msg, self.draw(), self.confirm(), self.message_box() et
self.run_external() sont fournis par nhmonedit.Editor.
"""

import os
import shlex
import shutil
import subprocess
import time

import nhmon_install as I
from nhmon_i18n import _

DEFAULT_HACKDIR = os.path.expanduser("~/nh/install/games/lib/nethackdir")
GAME_SESSION = "nhmonedit-jeu"
# ni introduction ni tutoriel : Ctrl-G doit arriver au jeu
GAME_OPTIONS = "!legacy,!tutorial"


def tmux(*args):
    """Commande tmux ; sa sortie, ou None en cas d'échec."""
    try:
        r = subprocess.run(["tmux"] + list(args), capture_output=True,
                           text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def game_command(hackdir):
    """Commande shell qui lance le jeu en mode wizard avec un personnage
    tiré au hasard."""
    opts = os.environ.get("NETHACKOPTIONS", "")
    # une valeur qui désigne un fichier remplace le .nethackrc : on n'y
    # touche pas
    if not opts.startswith(("/", "@")):
        opts = opts + "," + GAME_OPTIONS if opts else GAME_OPTIONS
    return "cd %s && HACKDIR=%s NETHACKOPTIONS=%s %s -D -@" % (
        shlex.quote(hackdir), shlex.quote(hackdir), shlex.quote(opts),
        shlex.quote(os.path.join(hackdir, "nethack")))


class Game:
    game_pane = None
    game_where = ""

    def hackdir(self):
        """Dossier du jeu installé : NHMONEDIT_HACKDIR, configuration,
        ~/nh/install/…, puis playground des sources."""
        for d in (os.environ.get("NHMONEDIT_HACKDIR", ""),
                  self.config.get("hackdir", ""), DEFAULT_HACKDIR,
                  os.path.join(self.src, "playground")):
            if d and os.access(os.path.join(d, "nethack"), os.X_OK):
                return d
        return None

    def game_alive(self):
        """Le panneau du jeu existe-t-il encore ? (il se ferme avec le
        jeu)"""
        if not self.game_pane:
            return False
        cmd = tmux("display-message", "-p", "-t", self.game_pane,
                   "#{pane_current_command}")
        if cmd is None:
            self.game_pane = None
        return bool(cmd)

    def outdated_game(self, hackdir):
        """Le jeu installé est-il plus ancien que monsters.h ?"""
        src = os.path.join(self.src, I.MONSTERS_H)
        exe = os.path.join(hackdir, "nethack")
        return os.path.isfile(src) and \
            os.path.getmtime(src) > os.path.getmtime(exe)

    def play(self):
        """j : essayer le monstre en jeu."""
        d = self.hackdir()
        if not d:
            self.message_box(_("Jeu introuvable"), [
                _("Pas d'exécutable nethack installé. Compilez (m) puis"),
                _("mettez à jour le jeu (U), ou indiquez son dossier avec"),
                "NHMONEDIT_HACKDIR."])
            return
        m = self.mon()
        if self.game_alive():
            if m:
                self.spawn_in_game(m)
            return
        lines = []
        if self.outdated_game(d):
            lines += [_("⚠ Le jeu installé est plus ancien que monsters.h :"),
                      _("  compilez (m) et mettez à jour (U) d'abord."), ""]
        if shutil.which("tmux"):
            if m:
                lines += [_("NetHack va s'ouvrir en mode wizard à côté de"),
                          _("l'éditeur, et « %s » sera créé près de vous.")
                          % m["name"],
                          _("Ensuite, j crée le monstre choisi dans la "
                            "partie en cours."), ""]
            lines += [_("Lancer le jeu maintenant ?")]
            if not self.confirm("\n".join(lines), _("Essayer en jeu")):
                return
            if self.start_game(d) and m:
                self.spawn_in_game(m)
            return
        names = [o["name"] for o in self.monsters]
        lines += [_("Mode wizard : Ctrl-G (créer un monstre), puis tapez le"),
                  _("nom ANGLAIS du monstre. « ; » pour le regarder."), ""]
        if names:
            lines += [_("Vos monstres : ") + ", ".join(names[:6]) +
                      ("…" if len(names) > 6 else ""), ""]
        lines += [_("(installez tmux pour que l'éditeur crée le monstre "
                    "lui-même)"), "", _("Lancer le jeu maintenant ?")]
        if not self.confirm("\n".join(lines), _("Essayer en jeu")):
            return
        cmd = "HACKDIR=%s %s -D" % (shlex.quote(d),
                                    shlex.quote(os.path.join(d, "nethack")))
        self.run_external(_("NetHack (mode wizard)"), cmd, d)

    def start_game(self, hackdir):
        """Lance NetHack dans tmux : un panneau ou une fenêtre de la
        session courante, sinon une session à part ouverte dans un
        nouveau terminal. Renvoie True si le jeu est prêt."""
        try:
            busy = subprocess.run(["pgrep", "-x", "nethack"],
                                  capture_output=True).returncode == 0
        except OSError:
            busy = False
        if busy:
            # même verrou de partie : un second jeu ne démarrerait pas
            self.msg = _("Une partie de NetHack est déjà en cours.")
            return False
        cmd = game_command(hackdir)
        attach = None
        if os.environ.get("TMUX"):
            here = os.environ.get("TMUX_PANE", "")
            width = int(tmux("display-message", "-p", "-t", here,
                             "#{window_width}") or 0)
            # assez large : panneau à droite (80 colonnes pour le jeu),
            # sinon une fenêtre tmux à part
            if width >= 170:
                pane = tmux("split-window", "-h", "-d", "-l", "82", "-t",
                            here, "-P", "-F", "#{pane_id}", cmd)
                where = _("panneau tmux à droite")
            else:
                pane = tmux("new-window", "-d", "-n", "nethack", "-P",
                            "-F", "#{pane_id}", cmd)
                where = _("fenêtre tmux « nethack »")
        else:
            tmux("kill-session", "-t", GAME_SESSION)
            pane = tmux("new-session", "-d", "-s", GAME_SESSION, "-x", "100",
                        "-y", "32", "-P", "-F", "#{pane_id}", cmd)
            attach = "tmux attach -t " + GAME_SESSION
            where = _("session tmux « %s »") % GAME_SESSION
            term = (os.environ.get("TERMINAL")
                    or shutil.which("x-terminal-emulator"))
            if pane and os.environ.get("DISPLAY") and term:
                try:
                    subprocess.Popen([term, "-e", "tmux", "attach", "-t",
                                      GAME_SESSION],
                                     stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     start_new_session=True)
                    attach = None
                except OSError:
                    pass
        if not pane:
            self.msg = _("Impossible de lancer le jeu dans tmux.")
            return False
        self.game_pane, self.game_where = pane, where
        self.msg = _("Lancement de NetHack…")
        self.draw()
        # attend que l'écran du jeu ne bouge plus
        last, stable, end = None, 0, time.time() + 15
        while time.time() < end and stable < 3:
            time.sleep(0.4)
            screen = tmux("capture-pane", "-p", "-t", pane)
            if screen is None:
                self.game_pane = None
                self.msg = _("Le jeu s'est arrêté au démarrage.")
                return False
            stable = stable + 1 if screen.strip() and screen == last else 0
            last = screen
        if attach:
            self.message_box(_("NetHack lancé"), [
                _("Le jeu tourne dans la session tmux « %s ».")
                % GAME_SESSION,
                _("Pour le voir, dans un autre terminal :"),
                "  " + attach])
        return True

    def spawn_in_game(self, m):
        """Ctrl-G puis le nom anglais : le monstre apparaît à côté du
        héros. Échap ferme d'abord un éventuel message en attente."""
        p = self.game_pane
        for _i in range(3):
            tmux("send-keys", "-t", p, "Escape")
            time.sleep(0.2)
        tmux("send-keys", "-t", p, "C-g")
        time.sleep(0.3)
        tmux("send-keys", "-t", p, "-l", m["name"])
        tmux("send-keys", "-t", p, "Enter")
        self.msg = _("« %s » créé dans la partie (%s) ; j en crée un "
                     "autre.") % (m["name"], self.game_where)
