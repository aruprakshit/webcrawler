# Docker Compose aliases for webcrawler project

# Short alias for running npm commands in nodejs-consumer container
alias dcrnpm="docker compose run --rm -u \$(id -u):\$(id -g) nodejs-consumer npm"
