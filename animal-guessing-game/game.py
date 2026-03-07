#!/usr/bin/env python3
"""
Animal Guessing Game
Uses a decision tree to guess your animal in as few questions as possible.
"""


def ask(question):
    while True:
        answer = input(f"{question} (yes/no): ").strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("Please answer yes or no.")


def guess(animal):
    print(f"\nMy guess: Is it a {animal}?")
    if ask("Am I right?"):
        print("I got it! Thanks for playing.\n")
        return True
    return False


def play():
    print("\n=== Animal Guessing Game ===")
    print("Think of an animal and I'll try to guess it!\n")

    if ask("Is it a mammal?"):
        if ask("Is it larger than a dog?"):
            if ask("Does it live in the ocean?"):
                if ask("Is it very large (bigger than a car)?"):
                    guess("whale") or guess("shark")
                else:
                    guess("dolphin") or guess("seal")
            elif ask("Does it have hooves?"):
                if ask("Does it have a mane or live in Africa?"):
                    if ask("Does it have stripes?"):
                        guess("zebra")
                    else:
                        guess("lion") or guess("giraffe") or guess("elephant")
                else:
                    if ask("Is it very tall?"):
                        guess("horse")
                    else:
                        guess("cow") or guess("pig")
            elif ask("Is it a big cat (has spots or stripes)?"):
                if ask("Does it have stripes?"):
                    guess("tiger")
                else:
                    guess("leopard") or guess("cheetah")
            elif ask("Does it have a trunk?"):
                guess("elephant")
            else:
                guess("bear") or guess("gorilla") or guess("hippo")
        else:
            if ask("Can it fly?"):
                guess("bat")
            elif ask("Is it a common household pet?"):
                if ask("Does it bark?"):
                    guess("dog")
                else:
                    guess("cat") or guess("rabbit")
            elif ask("Does it have a bushy tail and climb trees?"):
                guess("squirrel") or guess("monkey")
            else:
                guess("mouse") or guess("hedgehog") or guess("otter")

    elif ask("Does it have feathers?"):
        if ask("Can it fly?"):
            if ask("Is it a hunter (bird of prey)?"):
                if ask("Is it active at night?"):
                    guess("owl")
                else:
                    guess("eagle") or guess("hawk")
            elif ask("Can it talk or mimic sounds?"):
                guess("parrot")
            else:
                guess("robin") or guess("pigeon") or guess("duck")
        else:
            if ask("Is it very tall (taller than a person)?"):
                guess("ostrich") or guess("emu")
            else:
                guess("penguin")

    elif ask("Does it have scales?"):
        if ask("Does it live in water?"):
            if ask("Is it dangerous / very large?"):
                guess("shark") or guess("crocodile")
            else:
                guess("salmon") or guess("goldfish") or guess("tuna")
        else:
            if ask("Does it have legs?"):
                if ask("Is it large (longer than 1 meter)?"):
                    guess("crocodile") or guess("iguana")
                else:
                    guess("lizard") or guess("chameleon")
            else:
                guess("snake")

    elif ask("Does it have 6 legs?"):
        if ask("Does it have wings?"):
            if ask("Does it have colorful wings?"):
                guess("butterfly")
            else:
                guess("bee") or guess("dragonfly") or guess("beetle")
        else:
            guess("ant")

    elif ask("Does it have 8 legs?"):
        guess("spider") or guess("scorpion")

    elif ask("Does it live in water part of the time?"):
        guess("frog") or guess("turtle")

    else:
        guess("snail") or guess("worm")

    print("I couldn't figure it out! What was your animal?")
    animal = input("Answer: ").strip()
    print(f"Interesting! I'll have to remember {animal} next time.\n")


def main():
    while True:
        play()
        if not ask("Play again?"):
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
