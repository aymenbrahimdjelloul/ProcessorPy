from processorpy import Processor
from time import perf_counter

cpu = Processor(developer_mode=True)

s_time = perf_counter()
# print(cpu.tdp())
# print(cpu.get_cores(True))
print(cpu.name())
# print(cpu.vendor())
# print(cpu.lithography())
# print(cpu.tdp())
# print(cpu.get_max_clock(True))
# print(cpu.release_date())
# print(cpu.supported_memory_size())
# print(cpu.is_support_boost())
# print(cpu.is_virtualization())
# print(cpu.is_ecc())
# print(cpu.flags())
# print(cpu.socket())
# print(cpu.supported_memory_bandwidth())
# print(cpu.transistor_count())
# print(cpu.code_name())

# r = cpu.get_all_info(all_info=True)

# for k, v in r.items():
#     print(f"{k}  :  {v}")

print(f"Finished in : {perf_counter() - s_time:.4f}")
