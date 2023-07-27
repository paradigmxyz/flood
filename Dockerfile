# uploaded to GitHub Container Registry
# https://github.com/paradigmxyz/flood/pkgs/container/flood

# Stage 1: Install flood
FROM python:3.11.3-slim AS flood-builder
ENV USERNAME="flood"
ENV PATH="${PATH}:/home/${USERNAME}/.local/bin"
RUN adduser $USERNAME
USER $USERNAME

COPY ./ /home/$USERNAME/repos/flood/
WORKDIR /home/$USERNAME/repos/flood
RUN pip install --user --no-cache-dir ./

# Stage 2: Install vegeta
FROM debian:stable-slim AS vegeta-builder
RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir /vegeta
WORKDIR /vegeta
RUN wget https://github.com/tsenart/vegeta/releases/download/v12.8.4/vegeta_12.8.4_linux_amd64.tar.gz \
 && tar xzf vegeta_12.8.4_linux_amd64.tar.gz \
 && rm vegeta_12.8.4_linux_amd64.tar.gz

# Final stage: Combine flood and vegeta
FROM python:3.11.3-slim
ENV USERNAME="flood"
ENV PATH="${PATH}:/home/${USERNAME}/.local/bin"
RUN adduser $USERNAME
USER $USERNAME

COPY --from=flood-builder /home/$USERNAME/.local /home/$USERNAME/.local
COPY --from=vegeta-builder /vegeta/vegeta /home/$USERNAME/.local/bin/vegeta

WORKDIR /home/$USERNAME
ENTRYPOINT ["python", "-m", "flood"]
