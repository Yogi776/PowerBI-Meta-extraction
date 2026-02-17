FROM mcr.microsoft.com/dotnet/runtime:8.0
LABEL org.opencontainers.image.description="Containerized pbi-tools.core runtime"
ARG PBI_TOOLS_VERSION=1.2.0

WORKDIR /app

ENV DOTNET_CLI_TELEMETRY_OPTOUT=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y wget unzip git git-lfs ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN wget -O pbi-tools.zip "https://github.com/pbi-tools/pbi-tools/releases/download/${PBI_TOOLS_VERSION}/pbi-tools.core.${PBI_TOOLS_VERSION}_linux-x64.zip"
RUN unzip pbi-tools.zip -d pbi-tools
RUN rm -f pbi-tools.zip

RUN chmod +x /app/pbi-tools/pbi-tools.core

CMD ["/app/pbi-tools/pbi-tools.core", "info"]