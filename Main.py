from Core.Networking.Server import Server


def main():
    print("Brawl Stars v36 Private Server - Season 7")
    print("Featured brawler: Buzz")
    Server("0.0.0.0", 9339).start()


if __name__ == '__main__':
    main()
