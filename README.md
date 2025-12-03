#Валютный торговый хаб
#Установка и запуск
git clone https://github.com/Nightcor157/finalproject_Rozdorozhnyi_M25_555.git
cd finalproject_Rozdorozhnyi_M25_555

make install

make project

export EXCHANGERATE_API_KEY="Ваш API ключ для запросов"

#Примеры команд

register --username alice --password 1234
login --username alice --password 1234
buy --currency BTC --amount 0.1
sell --currency BTC --amount 0.05
show-portfolio
get-rate --from BTC --to USD
update-rates
show-rates


## Демонстрация работы

[![asciicast](https://asciinema.org/a/ArHXsjHhR0FRqBbfKXlOLyy32.svg)](https://asciinema.org/a/ArHXsjHhR0FRqBbfKXlOLyy32)

