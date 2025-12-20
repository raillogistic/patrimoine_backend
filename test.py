def largest_prime_factor(n):
    # Start with the smallest prime factor
    largest_factor = -1

    # Remove all factors of 2
    while n % 2 == 0:
        largest_factor = 2
        n //= 2

    # Try odd factors starting from 3
    factor = 3
    while factor * factor <= n:
        while n % factor == 0:
            largest_factor = factor
            n //= factor
        factor += 2

    # If n is a prime number greater than 2
    if n > 2:
        largest_factor = n

    return largest_factor


num = 600851475143
print("Largest prime factor of", num, "is:", largest_prime_factor(num))
