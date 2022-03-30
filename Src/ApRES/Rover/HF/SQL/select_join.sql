SELECT `measurements`.`measurement_id`, `apres_metadata`.`af_gain`
FROM `measurements`
INNER JOIN `apres_metadata`
ON `measurements`.`measurement_id`=`apres_metadata`.`measurement_id`
WHERE `measurements`.`valid` = 1