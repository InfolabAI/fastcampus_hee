def process_data(data, flag):
    if flag == 'SUM':
        res = 0
        for i in data:
            res += i
        return res
    elif flag == 'AVG':
        res = 0
        for i in data:
            res += i
        return res / len(data)
    else:
        return None
