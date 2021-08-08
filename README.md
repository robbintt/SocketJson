# Sockets, Threads, and Selectors

Finally got a working implementation:

- socketutf8.py
- SocketClientSelector.py - use selectors but not threads (although I know how now)
- SocketServerSelector.py - use selectors and threads to multiplex the client and the file descriptor

I believe I have a strong enough grasp to clean this up and get max cps locally.

Still not sure how many connections per second are reasonable to expect with a threaded selector socket impl on this macbook pro.

Goal is 10k qps... that would be nice...

# Threading the Client

The current client with 1 selector/fd per thread can get 1k cps but fails on 10k cps and still leaks about 600/10000 results, which must be a transaction implementation error.

It would be better to have a pool of threads and each thread to manage work from a controller until the controller tells the thread all the work is gone.

There doesn't really need to be a pool size, but it is loosely based around having 250 file descriptors available on macos. So 250 threads is overkill, the balance is between thread creation time and selector throughput in sequential events in a thread.
