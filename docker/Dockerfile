# Dockerfile — runner de vídeo (Manim 0.18 + FFmpeg + TinyTeX) sobre debian:12-slim.
#
# Público/open-source: NADA pessoal, nenhum secret, nenhum brand. Conteúdo do
# autor (paleta, mascote Capivara, QR) entra por volume read-only do host.
#
# Componentes:
#   - apt: ffmpeg, python3 (+venv/pip), git, curl, libs do Manim (cairo/pango/ffi)
#   - pip (venv em /opt/capy): manim==0.18.1 (pin em requirements.txt)
#   - TinyTeX em /opt/tinytex: apenas os pacotes LaTeX que o MathTex do Manim usa
#     (standalone, preview, doublestroke, relsize, cancel, enumitem, varwidth,
#      fancyhdr, amsmath, amssymb via core, dvisvgm, latexmk — MINIMAL)
#   - scripts/ e manim_skills/ copiados para /work/scripts
#
# Configuração do TinyTeX (tinha que ser listada): veja "TinyTeX packages" abaixo;
# referência oficial de projetos com MathTex: https://docs.manim.community/en/stable/tutorials/configuration.html
FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C.UTF-8 LANG=C.UTF-8 \
    PATH="/opt/capy/bin:/opt/tinytex/bin/x86_64-linux:/opt/tinytex/bin:${PATH}" \
    VIRTUAL_ENV=/opt/capy

# --- apt: runtime + libs do Manim (sem recommends)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        curl \
        ca-certificates \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libffi8 \
        shared-mime-info \
        fonts-noto-core \
        xz-utils \
        unzip \
        gcc \
        pkg-config \
        libcairo2-dev \
        libpango1.0-dev \
        libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# --- user não-proprietário capy (uid 1000)
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin capy

# --- virtualenv do runner + manim 0.18.1 (pin) + deps corrigidas (Trivy HIGH/CRITICAL)
COPY docker/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/capy && \
    /opt/capy/bin/pip install --no-cache-dir --upgrade pip setuptools urllib3 && \
    /opt/capy/bin/pip install --no-cache-dir -r /tmp/requirements.txt && \
    /opt/capy/bin/pip install --no-cache-dir -U 'urllib3>=2.8.0' 'setuptools>=78.1.1' && \
    rm -f /tmp/requirements.txt

# slim: remove toolchain/headers p/ build (wheels já compilados; runtime continua)
RUN apt-get update && apt-get purge -y --auto-remove gcc python3-dev libcairo2-dev libpango1.0-dev libglib2.0-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

# --- TinyTeX (instalador headless) + pacotes MINIMAL p/ MathTex
RUN curl -sL "https://yihui.org/tinytex/install-bin-unix.sh" | sh \
    && mv /root/.TinyTeX /opt/tinytex \
    && /opt/tinytex/bin/x86_64-linux/tlmgr option repository https://ftp.uni-erlangen.de/mirrors/CTAN/systems/texlive/tlnet \
    && /opt/tinytex/bin/x86_64-linux/tlmgr update --self \
    && /opt/tinytex/bin/x86_64-linux/tlmgr install \
        standalone preview doublestroke relsize cancel enumitem varwidth fancyhdr \
        rsfs mathtools microtype amsfonts dvisvgm latexmk \
        babel-english hyphen-english \
    && rm -rf /root/.cache /var/tmp/* /root/bin

# --- scripts + skill runtime
WORKDIR /work
COPY --chown=capy:capy scripts/ /work/scripts/
COPY --chown=capy:capy templates/ /work/templates/
COPY --chown=capy:capy references/ /work/references/

# permissões básicas
RUN chmod +x /work/scripts/*.sh /work/scripts/*.py 2>/dev/null || true

# --- HEALTHCHECK: manim + ffmpeg respondem
HEALTHCHECK --interval=60s --timeout=15s --start-period=10s --retries=2 \
    CMD /opt/capy/bin/python -c "import manim, sys; sys.exit(0 if manim.__version__.startswith('0.18') else 1)" \
        && /usr/bin/ffmpeg -version | head -1 >/dev/null || exit 1

# --- entrypoint: render_manim.py (o docker-run.sh sobrepõe o comando quando necessário)
ENTRYPOINT ["/opt/capy/bin/python", "/work/scripts/render_manim.py"]
CMD ["--help"]
