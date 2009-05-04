def my_test():
    for i in range(5):
        if i == 3:
            return
    finally:
        print 'clean up'

if __name__ == '__main__':
    my_test()