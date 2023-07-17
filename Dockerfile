FROM python:3.11.3

# create user
ENV USERNAME="flood"
ENV PATH="${PATH}:/home/${USERNAME}/bin"
RUN adduser $USERNAME
USER $USERNAME

# install flood
RUN mkdir /home/$USERNAME/repos
COPY ./ /home/$USERNAME/repos/flood/
WORKDIR /home/$USERNAME/repos/flood
RUN pip install ./

# install vegeta
RUN mkdir -p /home/$USERNAME/bin/vegeta_files
WORKDIR /home/$USERNAME/bin/vegeta_files
RUN wget https://github.com/tsenart/vegeta/releases/download/v12.8.4/vegeta_12.8.4_linux_amd64.tar.gz
RUN tar xzf vegeta_12.8.4_linux_amd64.tar.gz
RUN ln -s /home/$USERNAME/bin/vegeta_files/vegeta /home/$USERNAME/bin/vegeta

# run flood
WORKDIR /home/$USERNAME
ENTRYPOINT ["python", "-m", "flood"]
