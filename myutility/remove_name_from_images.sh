OLDIFS=$IFS; 
for s in *; 
do
	IFS="_"; 
	read -ra a <<< ${s}; 
	new_name=${a[0]}_${a[1]}; 
	IFS=$OLD_IFS; 
	echo $new_name; 
	mv $s ${new_name}-t1.nii.gz; 
done

