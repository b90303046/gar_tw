do_partition()
       |
     |prerun_partition()
     |	       |
     |         |____read_parameters_partition()
     |         |
     |	       |____check_parameters_partition()
     |         |
     |         |____read_parameters_global()
     |         |
     |	       |____read_data_partition()
     |         |
     |         |    (globals)
     |	       |____read_partition_groups()/read_partition_groupsPLS
     |         |
     |	       |____format_data_partition()
     |         |         | 
     | 	       |	 |___interpolate_mising_values()
     |	       |  	 |___ffill_values()
     |         |
     |         |__check_partition_groups()  
     |
     |run_partition()
     |     |
     |     |
     |     |___partition_retro()  [partition_retro.py]
     |     |       |
     |     |       |___cpdgrowth.py (cum_gr/yoy_gr)
     |     |       |
     |     |       |___ gen_cutoff ( gen_cutoff.py)
     |     |       |
     |     |       |
     |     |       |___ p_cutoff (partition_off.py)
     |     |       |
     |     |       |