#!/bin/bash

# === CONFIGURATION ===
TAUTULLI_API_KEY="yourapikey"
TAUTULLI_URL="http://localhost:8181"

# === COLORS ===
RED="\033[1;31m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
WHITE="\033[1;37m"
NC="\033[0m"

echo -e "${NC}"

# === FETCH AND PARSE ===
json=$(curl -s "${TAUTULLI_URL}/api/v2?apikey=${TAUTULLI_API_KEY}&cmd=get_activity")
active_streams=$(echo "$json" | jq '.response.data.sessions | length')
echo -e "${GREEN}${active_streams} active sessions${NC}\n"

# === LOOP THROUGH SESSIONS ===
echo "$json" | jq -c '.response.data.sessions[]' | while read -r session; do
  user=$(echo "$session" | jq -r '.user')
  location=$(echo "$session" | jq -r '.stream_location')
  ip=$(echo "$session" | jq -r '.ip_address')
  type=$(echo "$session" | jq -r '.media_type')
  title=$(echo "$session" | jq -r '.full_title')
  state=$(echo "$session" | jq -r '.state')
  player=$(echo "$session" | jq -r '.player')
  platform=$(echo "$session" | jq -r '.platform')
  version=$(echo "$session" | jq -r '.product_version')
  thumbnail=$(echo "$session" | jq -r '.thumb' | sed 's/\\//g')

  echo -e "${CYAN}User:${NC} $user"
  echo -e "${RED}Type:${NC} $type"
  echo -e "${GREEN}Title:${NC} $title"
  echo -e "${YELLOW}State:${NC} $state"
  echo -e "${WHITE}Player:${NC} ${player} - ${platform} ${version}"
  echo -e ""
done
